import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from ollama import ChatResponse

from glucotrust.assess import AssessmentUnavailable, GroqAssessor, OllamaAssessor
from glucotrust.pipeline import assess_claim, is_dosing_request
from glucotrust.retrieve import SearchHit
from glucotrust.validate import Assessment


@pytest.mark.parametrize('claim', ['Quanto de insulina devo tomar?', 'Quantas unidades de insulina devo aplicar?',
    'Qual é a minha dosagem de insulina?', 'Calcule minha dose de insulina', 'How much insulin should I take?'])
def test_bilingual_dosing_never_calls_translation_or_retrieval(claim):
    retriever, assessor = Mock(), Mock(model='mock')
    assert is_dosing_request(claim)
    assert assess_claim(claim, retriever, assessor, language='pt').status == 'blocked'
    assessor.translate_query.assert_not_called()
    retriever.search.assert_not_called()


def test_portuguese_uses_translation_for_both_searches_but_original_for_assessment(passage):
    claim, query = 'Baixo erro de previsão comprova segurança clínica?', 'Does low prediction error prove clinical safety?'
    retriever = Mock(search=Mock(return_value=[SearchHit(passage, .8)]))
    assessor = SimpleNamespace(model='mock', last_run={}, translate_query=Mock(return_value=(query, {'english_query':query})),
        assess=Mock(return_value=Assessment(verdict='insufficient', citations=[], explanation='Evidência insuficiente.')))
    literature = Mock(search=Mock(return_value=SimpleNamespace(hits=[], queries=['query'], note='none')))
    result = assess_claim(claim,retriever,assessor,language='pt',literature=literature)
    retriever.search.assert_called_once_with(query,k=3)
    literature.search.assert_called_once_with(query,k=3)
    assert assessor.assess.call_args.args[0] == claim
    assert result.run['query_translation']['english_query'] == query
    assert result.claim == claim


def test_failed_translation_is_unavailable_not_abstention():
    assessor = SimpleNamespace(model='mock', translate_query=Mock(side_effect=AssessmentUnavailable('Translation unavailable')))
    retriever=Mock()
    result=assess_claim('Afirmação em português',retriever,assessor,language='pt')
    assert result.status=='unavailable' and result.assessment is None
    retriever.search.assert_not_called()


@pytest.mark.parametrize('provider',['ollama','groq'])
def test_translation_uses_provider_specific_structured_schema(provider,tmp_path):
    query='Early diabetic kidney disease can occur without symptoms.'
    content=json.dumps({'english_query':query})
    if provider=='ollama':
        client=Mock()
        client.list.return_value=SimpleNamespace(models=[SimpleNamespace(model='test:latest',digest='digest')])
        client.chat.return_value=ChatResponse(model='test',done=True,done_reason='stop',message={'role':'assistant','content':content})
        assessor=OllamaAssessor(client=client,model='test',cache_dir=tmp_path)
        translated,trace=assessor.translate_query('Doença renal diabética inicial pode não apresentar sintomas.')
        assert 'english_query' in client.chat.call_args.kwargs['format']['properties']
    else:
        def handle(request):
            schema=json.loads(request.content)['response_format']['json_schema']['schema']
            assert schema['additionalProperties'] is False and 'english_query' in schema['properties']
            return httpx.Response(200,json={'model':'openai/gpt-oss-20b','choices':[{'finish_reason':'stop','message':{'content':content}}]})
        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            assessor=GroqAssessor(client=client,api_key='test-key',cache_dir=tmp_path)
            translated,trace=assessor.translate_query('Doença renal diabética inicial pode não apresentar sintomas.')
    assert translated==query and trace['provider']==provider
    assert not list(tmp_path.glob('*.json'))  # Translation is not cached as evidence/assessment.


def test_portuguese_ui_flow(passage, monkeypatch):
    from pathlib import Path
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.cache_resource.clear()
    query='Insulin helps glucose enter cells.'
    assessor=SimpleNamespace(model='mock',last_run={},translate_query=Mock(return_value=(query,{'english_query':query})),
        assess=Mock(return_value=Assessment(verdict='insufficient',citations=[],explanation='Evidência insuficiente.')))
    monkeypatch.setenv('GLUCOTRUST_PROVIDER','ollama')
    monkeypatch.setattr('glucotrust.assess.OllamaAssessor',lambda **kw:assessor)
    monkeypatch.setattr('glucotrust.retrieve.DenseRetriever',lambda *a,**kw:Mock(search=Mock(return_value=[SearchHit(passage,.8)])))
    at=AppTest.from_file(Path('app.py').resolve()).run()
    at.selectbox[0].select('Português')
    at.checkbox[0].uncheck()
    at.text_area[0].input('Insulina ajuda a glicose a entrar nas células.')
    at.button(key="assess_claim").click().run()
    assert not at.exception
    assessor.translate_query.assert_called_once()
    assert any('Evidência insuficiente.' in item.value for item in at.markdown)


def test_requested_response_language_is_explicit_and_cache_isolated(passage,tmp_path):
    client=Mock()
    client.list.return_value=SimpleNamespace(models=[SimpleNamespace(model='test:latest',digest='digest')])
    client.chat.return_value=ChatResponse(model='test',done=True,done_reason='stop',message={'role':'assistant','content':json.dumps(
        {'verdict':'insufficient','citations':[],'explanation':'Sem evidência.'})})
    assessor=OllamaAssessor(client=client,model='test',cache_dir=tmp_path)
    assessor.assess('claim',[passage])
    assessor.assess('claim',[passage],language='pt')
    assert client.chat.call_count==2
    assert assessor.last_run['identity']['explanation_language']=='pt'
    body=json.loads(client.chat.call_args.kwargs['messages'][1]['content'])
    assert 'Português' in body['explanation_language']
