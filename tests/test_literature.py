import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from glucotrust.assess import AssessmentUnavailable
from glucotrust.literature import EuropePMCLiterature, LiteratureUnavailable, LiteratureResult, search_terms
from glucotrust.pipeline import assess_claim
from glucotrust.retrieve import SearchHit
from glucotrust.validate import Assessment, Citation


def test_api_search_fulltext_and_traceability():
    requests = []
    def handle(request):
        requests.append(request)
        if request.url.path.endswith('/search'):
            return httpx.Response(200, json={'resultList': {'result': [{
                'id': '123', 'source': 'MED', 'title': 'Clarke error grid analysis', 'pmcid': 'PMC123',
                'pubYear': '2024', 'isOpenAccess': 'Y',
                'abstractText': '<p>The Clarke error grid categorizes glucose errors into clinically meaningful zones.</p>'}]}})
        assert request.url.path.endswith('/PMC123/fullTextXML')
        return httpx.Response(200, text='<article><body><sec><p>Zone D of the Clarke error grid represents dangerous failures to detect and treat abnormal glucose.</p></sec></body></article>')
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = EuropePMCLiterature(client).search('A zode D Clarke error grid prediction is safe')
    assert len(requests) == 2
    assert result.hits
    assert all(h.passage.provenance_status == 'retrieved' for h in result.hits)
    assert all(h.passage.url == 'https://europepmc.org/article/MED/123' for h in result.hits)
    assert any('Zone D' in h.passage.text for h in result.hits)
    assert 'safe' not in search_terms('Clarke error grid is safe')


def test_relaxed_query_and_no_results():
    queries = []
    def handle(request):
        queries.append(request.url.params['query'])
        return httpx.Response(200, json={'resultList': {'result': []}})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        found = EuropePMCLiterature(client).search('Glucose forecasting is safe')
    assert len(queries) == 2 and ' OR ' in queries[1]
    assert not found.hits


def test_fulltext_failure_retains_abstract():
    def handle(request):
        if request.url.path.endswith('/search'):
            return httpx.Response(200, json={'resultList': {'result': [{'id':'1','source':'MED',
                'pmcid':'PMC1', 'isOpenAccess':'Y', 'title':'Glucose',
                'abstractText':'This is a usable research abstract containing sufficient words about glucose.'}]}})
        return httpx.Response(404)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        found = EuropePMCLiterature(client).search('Glucose')
    assert found.hits and found.hits[0].passage.qtype == 'abstract'
    assert 'unavailable' in found.note


@pytest.mark.parametrize('payload', [None, {'wrong':[]}, {'resultList': {'result': None}}])
def test_bad_search_response(payload):
    def handle(request):
        return httpx.Response(503) if payload is None else httpx.Response(200, json=payload)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(LiteratureUnavailable):
            EuropePMCLiterature(client).search('glucose')


def setup_flow(passage):
    retriever = Mock(search=Mock(return_value=[SearchHit(passage, 1)]))
    assessor = SimpleNamespace(model='test',last_run={},assess=Mock())
    external = passage.model_copy(update={'passage_id':'external#p1','source_type':'research','provenance_status':'retrieved'})
    search = Mock(search=Mock(return_value=LiteratureResult([SearchHit(external, 2)],['glucose'],'Completed.')))
    insufficient = Assessment(verdict='insufficient',citations=[],explanation='Missing evidence.')
    supported = Assessment(verdict='supported',citations=[Citation(passage_id=external.passage_id,
        quote='Insulin helps glucose enter cells.')],explanation='External evidence.')
    return retriever, assessor, search, insufficient, supported


def test_fallback_reassesses_and_validates(passage):
    retriever, assessor, search, insufficient, supported = setup_flow(passage)
    assessor.assess.side_effect = [insufficient,supported]
    result = assess_claim('Claim',retriever,assessor,literature=search)
    assert result.assessment.verdict == 'supported'
    assert len(result.hits) == 2 and result.literature['status'] == 'assessed'
    assert result.literature['local_assessment']['verdict'] == 'insufficient'
    assert result.literature['passages'][0]['provenance_status'] == 'retrieved'
    supported.citations[0].quote = 'Invented quote'
    assessor.assess.side_effect = [insufficient,supported]
    result = assess_claim('Claim',retriever,assessor,literature=search)
    assert result.assessment.validation_failed
    assert result.assessment.verdict == 'insufficient'


@pytest.mark.parametrize('outcome', ['no_results','search_failure','assessment_failure'])
def test_fallback_failure_preserves_local_result(passage,outcome):
    retriever, assessor, search, insufficient, supported = setup_flow(passage)
    assessor.assess.side_effect = [insufficient, AssessmentUnavailable('Failed second assessment')]
    if outcome == 'no_results': search.search.return_value = LiteratureResult()
    if outcome == 'search_failure': search.search.side_effect = LiteratureUnavailable('offline')
    result = assess_claim('Claim',retriever,assessor,literature=search)
    assert result.assessment.verdict == 'insufficient'
    assert result.assessment.explanation == 'Missing evidence.'
    assert result.literature['status'] in {'no_results','unavailable','assessment_unavailable'}


@pytest.mark.parametrize('mode', ['supported','oracle','blocked','disabled','unavailable'])
def test_no_external_search_when_inappropriate(passage,mode):
    retriever, assessor, search, insufficient, _ = setup_flow(passage)
    assessor.assess.return_value = insufficient if mode != 'supported' else Assessment(
        verdict='supported',citations=[Citation(passage_id=passage.passage_id,quote='Insulin helps glucose enter cells.')],explanation='Direct.')
    if mode == 'unavailable': assessor.assess.side_effect = AssessmentUnavailable('offline')
    assess_claim('How much insulin should I take?' if mode == 'blocked' else 'Claim', retriever,assessor,
                 passages=[passage] if mode == 'oracle' else None,
                 literature=None if mode == 'disabled' else search)
    search.search.assert_not_called()
