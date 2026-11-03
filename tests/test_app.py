from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from glucotrust.retrieve import SearchHit
from glucotrust.validate import Assessment, Citation


@pytest.mark.parametrize("custom_feedback_path", [False, True])
@pytest.mark.parametrize("provider", ["ollama", "groq"])
def test_claim_to_feedback(passage, monkeypatch, tmp_path, custom_feedback_path, provider):
    monkeypatch.setenv("GLUCOTRUST_PROVIDER", provider)
    feedback_path = tmp_path / "runtime" / "feedback.jsonl" if custom_feedback_path else Path("feedback.jsonl").resolve()
    if custom_feedback_path:
        monkeypatch.setenv("GLUCOTRUST_FEEDBACK_PATH", str(feedback_path))
    else:
        monkeypatch.delenv("GLUCOTRUST_FEEDBACK_PATH", raising=False)
    retriever = Mock()
    retriever.search.return_value = [SearchHit(passage, .9)]
    assessor = SimpleNamespace(model="mock-model", last_run={}, assess=Mock(return_value=Assessment(
        verdict="supported", citations=[Citation(passage_id=passage.passage_id, quote="Insulin helps glucose enter cells.")], explanation="Direct evidence.")))
    monkeypatch.setattr("glucotrust.retrieve.DenseRetriever", lambda *args, **kwargs: retriever)
    monkeypatch.setattr("glucotrust.assess." + ("GroqAssessor" if provider == "groq" else "OllamaAssessor"), lambda **kwargs: assessor)
    feedback = Mock()
    monkeypatch.setattr("glucotrust.feedback.save_feedback", feedback)
    at = AppTest.from_file(Path("app.py").resolve()).run()
    assert not at.exception
    if provider == "groq":
        assert any("sent to Groq" in item.value for item in at.caption)
    at.text_area[0].input("Insulin helps glucose enter cells.")
    at.button(key="assess_claim").click().run()
    assert not at.exception
    assert any('class="verdict supported">Supported</div>' in item.value for item in at.html)
    assert any("Archived dataset record" in item.value for item in at.caption)
    assert any("<mark>Insulin helps glucose enter cells.</mark>" in item.value for item in at.markdown)
    at.text_area[1].input("Reviewed the quote")
    at.button[-1].click().run()
    feedback.assert_called_once()
    assert feedback.call_args.args[1:3] == (True, "Reviewed the quote")
    assert feedback.call_args.args[3] == feedback_path
    assert not at.exception


def test_empty_claim_and_dosing_block():
    at = AppTest.from_file(Path("app.py").resolve()).run()
    at.button(key="assess_claim").click().run()
    assert at.error[0].value == "Enter a claim first."
    at.text_area[0].input("How much insulin should I take?")
    at.button(key="assess_claim").click().run()
    assert "cannot provide" in at.info[0].value
    assert not at.exception


def test_literature_fallback_ui(passage, monkeypatch):
    from glucotrust.literature import LiteratureResult
    external = passage.model_copy(update={"passage_id":"europepmc:MED:1#p1", "source_type":"research",
        "provenance_status":"retrieved", "source":"Europe PMC · MED:1 · abstract"})
    retriever = Mock(search=Mock(return_value=[SearchHit(passage,.5)]))
    assessor = SimpleNamespace(model="mock",last_run={},assess=Mock(side_effect=[
        Assessment(verdict="insufficient",citations=[],explanation="No local evidence."),
        Assessment(verdict="contradicted",citations=[Citation(passage_id=external.passage_id,
            quote="Insulin helps glucose enter cells.")],explanation="Research contradicts claim.")]))
    search = Mock(search=Mock(return_value=LiteratureResult([SearchHit(external,1)],["test query"],"Literature search completed.")))
    monkeypatch.setattr("glucotrust.retrieve.DenseRetriever",lambda *a,**kw:retriever)
    monkeypatch.setattr("glucotrust.assess.OllamaAssessor",lambda **kw:assessor)
    monkeypatch.setattr("glucotrust.literature.EuropePMCLiterature",lambda:search)
    at = AppTest.from_file(Path("app.py").resolve()).run()
    at.text_area[0].input("Claim requiring research")
    at.button(key="assess_claim").click().run()
    assert not at.exception
    assert any('class="verdict contradicted">Contradicted</div>' in item.value for item in at.html)
    assert any("Retrieved research excerpt" in c.value for c in at.caption)
    assert any("Literature search completed" in i.value for i in at.info)
    search.search.assert_called_once()


def test_scoped_current_reference_is_separate_from_model_evidence(passage, monkeypatch):
    import streamlit as st
    from glucotrust.assess import AssessmentUnavailable
    st.cache_resource.clear()  # Other AppTest instances may cache a different mocked retriever.
    passage = passage.model_copy(update={"passage_id": "5_NIDDK_QA:0000033-6#p1"})
    retriever = Mock(search=Mock(return_value=[SearchHit(passage, .9)]))
    assessor = SimpleNamespace(model="mock", last_run={}, assess=Mock(
        side_effect=AssessmentUnavailable("Model unavailable")))
    monkeypatch.setenv("GLUCOTRUST_PROVIDER", "ollama")
    monkeypatch.setattr("glucotrust.retrieve.DenseRetriever", lambda *a, **kw: retriever)
    monkeypatch.setattr("glucotrust.assess.OllamaAssessor", lambda **kw: assessor)
    at = AppTest.from_file(Path("app.py").resolve()).run()
    at.text_area[0].input("Kidney disease can be asymptomatic.")
    at.button(key="assess_claim").click().run()
    assert not at.exception
    assert any("Current reference: Diabetic Kidney Disease" in link.label for link in at.get("link_button"))
    assert any("historical dataset content" in item.value for item in at.caption)
    assert any("was not supplied to the model" in item.value for item in at.caption)
    assert assessor.assess.call_args.args[1] == [passage]
