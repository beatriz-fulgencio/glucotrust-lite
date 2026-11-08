import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from ollama import ChatResponse, ResponseError

from glucotrust.assess import AssessmentUnavailable, OllamaAssessor, OPTIONS
from glucotrust.feedback import save_feedback
from glucotrust.pipeline import assess_claim
from glucotrust.retrieve import SearchHit
from glucotrust.validate import validate_assessment


def client_response(passage, stop_reason="stop", content=None):
    output = dict(verdict="supported", citations=[dict(passage_id=passage.passage_id,
                  quote="Insulin helps glucose enter cells.")], explanation="Direct evidence.")
    client = Mock()
    client.list.return_value = SimpleNamespace(models=[SimpleNamespace(
        model="test:latest", digest="sha256:first")])
    client.chat.return_value = ChatResponse(model="test:latest", done=True, done_reason=stop_reason,
        message=dict(role="assistant", content=json.dumps(output) if content is None else content),
        prompt_eval_count=20, eval_count=30, total_duration=100)
    return client


def assessor_for(client, tmp_path):
    return OllamaAssessor(client=client, model="test", cache_dir=tmp_path)


def test_cache_and_invalidation(passage, tmp_path):
    client = client_response(passage)
    assessor = assessor_for(client, tmp_path)
    assessor.assess("claim", [passage])
    assessor.assess("claim", [passage])
    assert client.chat.call_count == 1
    assert assessor.last_run["cache_hit"]
    kwargs = client.chat.call_args.kwargs
    assert kwargs["options"] == OPTIONS
    assert kwargs["format"]["properties"]["verdict"]["enum"] == ["supported", "contradicted", "insufficient"]
    assert kwargs["stream"] is False
    assessor.assess("claim", [passage.model_copy(update={"text": passage.text + " Changed text"})])
    client.list.return_value.models[0].digest = "sha256:second"
    assessor.assess("claim", [passage])
    assert client.chat.call_count == 3
    assert assessor.last_run["identity"]["provider"] == "ollama"


@pytest.mark.parametrize("stop,content", [("length", None), ("stop", ""),
    ("stop", "I cannot help"), ("stop", '{}'), ("stop", '{"verdict":"wrong"}')])
def test_bad_response_not_abstention(passage, tmp_path, stop, content):
    assessor = assessor_for(client_response(passage, stop, content), tmp_path)
    with pytest.raises(AssessmentUnavailable):
        assessor.assess("claim", [passage])
    assert not list(tmp_path.glob("*.json"))


@pytest.mark.parametrize("error", [ConnectionError(), TimeoutError(), ResponseError("missing", 404)])
def test_server_failure(passage, tmp_path, error):
    client = client_response(passage)
    client.chat.side_effect = error
    with pytest.raises(AssessmentUnavailable, match="Check Ollama"):
        assessor_for(client, tmp_path).assess("claim", [passage])


def test_missing_model(passage, tmp_path):
    client = client_response(passage)
    client.list.return_value.models = []
    with pytest.raises(AssessmentUnavailable, match="ollama pull test"):
        assessor_for(client, tmp_path).assess("claim", [passage])
    client.chat.assert_not_called()


def test_pipeline_feedback_and_dosing(passage, tmp_path):
    retriever = Mock()
    retriever.search.return_value = [SearchHit(passage, 1)]
    client = client_response(passage)
    assessor = assessor_for(client, tmp_path / "cache")
    result = assess_claim("Insulin helps glucose enter cells.", retriever, assessor)
    assert result.assessment.verdict == "supported"
    assert result.model == "test:latest"
    feedback = tmp_path / "feedback.jsonl"
    save_feedback(result, True, "Reviewed", feedback)
    row = json.loads(feedback.read_text())
    assert row["correct"] and row["passage_ids"] == [passage.passage_id]
    retriever.reset_mock()
    client.chat.reset_mock()
    blocked = assess_claim("How much insulin should I take?", retriever, assessor)
    assert blocked.status == "blocked" and blocked.assessment is None
    retriever.search.assert_not_called()
    client.chat.assert_not_called()


@pytest.mark.parametrize("contents", ["broken", "[]", "null", "42", "{}", '{"assessment": {}}'])
def test_corrupt_cache_recomputed(passage, tmp_path, contents):
    client = client_response(passage)
    assessor = assessor_for(client, tmp_path)
    assessor.assess("claim", [passage])
    next(tmp_path.glob("*.json")).write_text(contents)
    assessor.assess("claim", [passage])
    assert client.chat.call_count == 2


@pytest.mark.parametrize("error", [PermissionError, FileNotFoundError])
def test_unreadable_cache_does_not_prevent_inference(passage, tmp_path, monkeypatch, error):
    client = client_response(passage)
    assessor = assessor_for(client, tmp_path)
    assessor.assess("claim", [passage])
    def fail_read(*args, **kwargs):
        raise error("Cache unavailable")
    monkeypatch.setattr(Path, "read_text", fail_read)
    result = assessor.assess("claim", [passage])
    assert result.verdict == "supported" and client.chat.call_count == 2
    assert not assessor.last_run["cache_hit"]


def test_failed_cache_write_and_cleanup_keep_completed_assessment(passage, tmp_path, monkeypatch):
    client = client_response(passage)
    def fail(*args, **kwargs):
        raise PermissionError("Cache unavailable")
    monkeypatch.setattr(Path, "replace", fail)
    monkeypatch.setattr(Path, "unlink", fail)
    assert assessor_for(client, tmp_path).assess("claim", [passage]).verdict == "supported"


@pytest.mark.parametrize("damage", ["identity", "response", "citations"])
def test_damaged_cache_metadata_or_citations_recomputed(passage, tmp_path, damage):
    client = client_response(passage)
    assessor = assessor_for(client, tmp_path)
    assessor.assess("claim", [passage])
    cache = next(tmp_path.glob("*.json"))
    record = json.loads(cache.read_text())
    if damage == "citations":
        record["assessment"]["citations"][0]["quote"] = "Invented quote"
    else:
        record[damage] = []
    cache.write_text(json.dumps(record))
    result = assessor.assess("claim", [passage])
    assert not validate_assessment(result, [passage]).validation_failed
    assert client.chat.call_count == 2


def test_incomplete_flag(passage, tmp_path):
    client = client_response(passage)
    client.chat.return_value.done = False
    with pytest.raises(AssessmentUnavailable, match="did not complete"):
        assessor_for(client, tmp_path).assess("claim", [passage])


def test_citation_retry_preserves_exact_validation(passage, tmp_path):
    client = client_response(passage)
    valid = client.chat.return_value
    invalid = valid.model_copy(deep=True)
    output = json.loads(invalid.message.content)
    output["citations"][0]["quote"] = "Insulin moves sugar into cells."
    invalid.message.content = json.dumps(output)
    client.chat.side_effect = [invalid, valid]
    assessor = assessor_for(client, tmp_path)
    result = assessor.assess("Insulin helps glucose enter cells.", [passage])
    assert validate_assessment(result, [passage]).verdict == "supported"
    assert client.chat.call_count == 2
    assert assessor.last_run["citation_retry"]["validation_errors"]
    assert len(client.chat.call_args.kwargs["messages"]) == 4
    assessor.assess("Insulin helps glucose enter cells.", [passage])
    assert client.chat.call_count == 2
    assert assessor.last_run["cache_hit"]


@pytest.mark.parametrize("repair", ["invalid", "unavailable", "malformed", "incomplete"])
def test_failed_citation_retry_cannot_create_support(passage, tmp_path, repair):
    client = client_response(passage)
    invalid = client.chat.return_value.model_copy(deep=True)
    output = json.loads(invalid.message.content)
    output["citations"][0]["quote"] = "Insulin cures diabetes."
    invalid.message.content = json.dumps(output)
    retry = invalid.model_copy(deep=True)
    if repair == "malformed":
        retry.message.content = "{}"
    elif repair == "incomplete":
        retry.done_reason = "length"
    client.chat.side_effect = [invalid, TimeoutError() if repair == "unavailable" else retry]
    assessor = assessor_for(client, tmp_path)
    result = validate_assessment(assessor.assess("claim", [passage]), [passage])
    assert result.verdict == "insufficient" and result.validation_failed
    assert client.chat.call_count == 2
    assert not list(tmp_path.glob("*.json"))
