import json
from contextlib import contextmanager
from unittest.mock import Mock

import httpx
import pytest

from glucotrust.assess import AssessmentUnavailable, GroqAssessor, create_assessor
from glucotrust.pipeline import assess_claim
from glucotrust.validate import validate_assessment


def completion(quote="Insulin helps glucose enter cells.", finish="stop", content=None):
    output = dict(verdict="supported", citations=[dict(passage_id="p1", quote=quote)], explanation="Direct evidence.")
    return dict(model="openai/gpt-oss-20b", choices=[dict(finish_reason=finish,
        message=dict(content=json.dumps(output) if content is None else content))],
        usage=dict(prompt_tokens=100, completion_tokens=40))


@contextmanager
def hosted(tmp_path, handler, **kwargs):
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        yield GroqAssessor(client=client, api_key="unit-test-secret", cache_dir=tmp_path, **kwargs)


def test_strict_http_contract_cache_and_secret_exclusion(passage, tmp_path):
    passage = passage.model_copy(update={"passage_id": "p1"})
    requests = []
    def handle(request):
        requests.append(request)
        assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer unit-test-secret"
        body = json.loads(request.content)
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
        assert body["reasoning_effort"] == "low"
        assert body["stream"] is False
        assert body["max_completion_tokens"] == 2048
        return httpx.Response(200, json=completion())
    with hosted(tmp_path, handle) as assessor:
        result = assessor.assess("claim", [passage])
        assert validate_assessment(result, [passage]).verdict == "supported"
        assessor.assess("claim", [passage])
        assert len(requests) == 1 and assessor.last_run["cache_hit"]
        assert assessor.last_run["identity"]["provider"] == "groq"
        assert assessor.last_run["response"]["raw"]["usage"]["completion_tokens"] == 40
        assert "unit-test-secret" not in next(tmp_path.glob("*.json")).read_text()


@pytest.mark.parametrize("status,expected", [(429, "usage limit"), (401, "authentication"),
                                             (403, "authentication"), (503, "Hosted assessment failed")])
def test_http_failures_are_unavailable_and_hide_response_body(passage, tmp_path, status, expected):
    def handle(request):
        return httpx.Response(status, json={"error": {"message": "unit-test-secret private error"}})
    with hosted(tmp_path, handle) as assessor:
        with pytest.raises(AssessmentUnavailable, match=expected) as caught:
            assessor.assess("claim", [passage])
        assert "unit-test-secret" not in str(caught.value)
        assert not list(tmp_path.glob("*.json"))


@pytest.mark.parametrize("finish,content", [("length", None), ("stop", "{}"),
                                           ("stop", ""), ("stop", "Refused")])
def test_malformed_or_incomplete_is_not_insufficient(passage, tmp_path, finish, content):
    with hosted(tmp_path, lambda request: httpx.Response(200, json=completion(finish=finish, content=content))) as assessor:
        with pytest.raises(AssessmentUnavailable):
            assessor.assess("claim", [passage])
        assert not list(tmp_path.glob("*.json"))


@pytest.mark.parametrize("repair_succeeds", [True, False])
def test_citation_repair_retains_validator(passage, tmp_path, repair_succeeds):
    passage = passage.model_copy(update={"passage_id": "p1"})
    requests = []
    def handle(request):
        requests.append(json.loads(request.content))
        if len(requests) == 2 and repair_succeeds:
            return httpx.Response(200, json=completion())
        return httpx.Response(200, json=completion(quote="Insulin cures diabetes."))
    with hosted(tmp_path, handle) as assessor:
        result = validate_assessment(assessor.assess("claim", [passage]), [passage])
        assert len(requests) == 2 and len(requests[-1]["messages"]) == 4
        assert result.verdict == ("supported" if repair_succeeds else "insufficient")
        assert result.validation_failed is not repair_succeeds
        assert bool(list(tmp_path.glob("*.json"))) is repair_succeeds


def test_revision_invalidates_hosted_cache(passage, tmp_path, monkeypatch):
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=completion(content=json.dumps(dict(
            verdict="insufficient", citations=[], explanation="No evidence."))))
    with hosted(tmp_path, handle) as assessor:
        assessor.assess("claim", [passage])
        monkeypatch.setenv("GLUCOTRUST_GROQ_REVISION", "next")
        assessor.assess("claim", [passage])
        assert len(requests) == 2


def test_missing_key_and_dosing_never_contact_provider(passage, tmp_path):
    client = Mock()
    assessor = GroqAssessor(client=client, api_key="", cache_dir=tmp_path)
    with pytest.raises(AssessmentUnavailable, match="Set GROQ_API_KEY"):
        assessor.assess("claim", [passage])
    retriever = Mock()
    result = assess_claim("How much insulin should I take?", retriever, assessor)
    assert result.status == "blocked"
    retriever.search.assert_not_called()
    client.post.assert_not_called()


def test_factory_selects_hosted_model_without_local_model_env(monkeypatch):
    monkeypatch.setenv("GLUCOTRUST_PROVIDER", "groq")
    monkeypatch.setenv("GLUCOTRUST_MODEL", "local-only-model")
    assert create_assessor().model == "openai/gpt-oss-20b"
    monkeypatch.setenv("GLUCOTRUST_PROVIDER", "invalid")
    with pytest.raises(ValueError, match="must be ollama or groq"):
        create_assessor()
