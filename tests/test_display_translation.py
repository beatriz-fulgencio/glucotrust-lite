import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from glucotrust.assess import AssessmentUnavailable, GroqAssessor
from glucotrust.retrieve import SearchHit
from glucotrust.validate import Assessment, Citation


def app_with_result(passage, monkeypatch, *, failure=False):
    st.cache_resource.clear()
    original=Assessment(verdict='supported',explanation='Insulin helps glucose enter cells.',citations=[
        Citation(passage_id=passage.passage_id,quote='Insulin helps glucose enter cells.')])
    assessor=SimpleNamespace(model='mock',last_run={},assess=Mock(return_value=original),
        translate_summary=Mock(side_effect=AssessmentUnavailable('Offline') if failure else None,
                               return_value='A insulina ajuda a glicose a entrar nas células.'))
    retriever=Mock(search=Mock(return_value=[SearchHit(passage,.8)]))
    monkeypatch.setenv('GLUCOTRUST_PROVIDER','ollama')
    monkeypatch.setattr('glucotrust.assess.OllamaAssessor',lambda **kw:assessor)
    monkeypatch.setattr('glucotrust.retrieve.DenseRetriever',lambda *a,**kw:retriever)
    at=AppTest.from_file(Path('app.py').resolve()).run()
    at.text_area[0].input('Insulin helps glucose enter cells.')
    at.button(key='assess_claim').click().run()
    return at,assessor,retriever,original


def test_translation_button_changes_title_and_summary_without_reassessment(passage,monkeypatch):
    at,assessor,retriever,original=app_with_result(passage,monkeypatch)
    at.button(key='toggle_portuguese').click().run()
    assert not at.exception
    assert at.title[0].value=='Verifique uma afirmação com base nas evidências'
    assert any('Sustentada pelas evidências' in x.value for x in at.html)
    assert any('A insulina ajuda' in x.value for x in at.markdown)
    assert any('<mark>Insulin helps glucose enter cells.</mark>' in x.value for x in at.markdown)
    assert at.session_state.result.assessment.explanation==original.explanation
    assessor.assess.assert_called_once()
    retriever.search.assert_called_once()
    assessor.translate_summary.assert_called_once_with(original.explanation, quotes=[c.quote for c in original.citations])
    at.button(key='toggle_portuguese').click().run()
    assert at.title[0].value=='Check a claim against the evidence'
    at.button(key='toggle_portuguese').click().run()
    assert assessor.translate_summary.call_count==1


def test_translation_failure_retains_original_summary(passage,monkeypatch):
    at,assessor,_,original=app_with_result(passage,monkeypatch,failure=True)
    at.button(key='toggle_portuguese').click().run()
    assert not at.exception
    assert any('Não foi possível traduzir' in x.value for x in at.warning)
    assert at.session_state.result.assessment.explanation==original.explanation
    assert any(original.explanation==x.value for x in at.markdown)


def test_translate_summary_uses_presentation_only_schema(tmp_path):
    def handle(request):
        data=json.loads(request.content)
        schema=data['response_format']['json_schema']['schema']
        assert list(schema['properties'])==['explanation']
        body=json.loads(data['messages'][1]['content'])
        assert body=={'explanation':'The evidence is insufficient.'}
        assert 'Do not reassess' in data['messages'][0]['content']
        return httpx.Response(200,json={'model':'openai/gpt-oss-20b','choices':[{
            'finish_reason':'stop','message':{'content':json.dumps({'explanation':'As evidências são insuficientes.'})}}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        assessor=GroqAssessor(client=client,api_key='test-key',cache_dir=tmp_path)
        assert assessor.translate_summary('The evidence is insufficient.')=='As evidências são insuficientes.'
        assert not list(tmp_path.glob('*.json'))


@pytest.mark.parametrize("preserve", [True, False])
def test_summary_quotes_are_restored_exactly_or_translation_rejected(tmp_path, preserve):
    quote="People with kidney disease do not have symptoms."
    def handle(request):
        original=json.loads(json.loads(request.content)['messages'][1]['content'])['explanation']
        assert quote not in original and '__GLUCOTRUST_QUOTE_0__' in original
        text='O trecho afirma: __GLUCOTRUST_QUOTE_0__' if preserve else 'O trecho afirma algo diferente.'
        return httpx.Response(200,json={'model':'openai/gpt-oss-20b','choices':[{
            'finish_reason':'stop','message':{'content':json.dumps({'explanation':text})}}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        assessor=GroqAssessor(client=client,api_key='test-key',cache_dir=tmp_path)
        if preserve:
            assert quote in assessor.translate_summary('The source states: '+quote,quotes=[quote])
        else:
            with pytest.raises(AssessmentUnavailable,match='preserve source quotations'):
                assessor.translate_summary('The source states: '+quote,quotes=[quote])


def test_failed_translation_can_be_retried_without_reassessment(passage, monkeypatch):
    at,assessor,retriever,original=app_with_result(passage,monkeypatch,failure=True)
    at.button(key='toggle_portuguese').click().run()
    assert any('Não foi possível traduzir' in x.value for x in at.warning)
    assessor.translate_summary.side_effect=None
    at.button(key='retry_summary_translation').click().run()
    assert not at.exception
    assert any('A insulina ajuda' in x.value for x in at.markdown)
    assert assessor.translate_summary.call_count==2
    assessor.assess.assert_called_once()
    retriever.search.assert_called_once()
    assert at.session_state.result.assessment.explanation==original.explanation


def test_toggle_back_retries_failed_translation_and_explains_quota(passage,monkeypatch):
    at,assessor,_,_=app_with_result(passage,monkeypatch)
    assessor.translate_summary.side_effect=AssessmentUnavailable("The hosted model's usage limit has been reached.")
    at.button(key='toggle_portuguese').click().run()
    assert any('limite de uso' in x.value for x in at.warning)
    at.button(key='toggle_portuguese').click().run()
    assessor.translate_summary.side_effect=None
    at.button(key='toggle_portuguese').click().run()
    assert any('A insulina ajuda' in x.value for x in at.markdown)
    assert assessor.translate_summary.call_count==2
