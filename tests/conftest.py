import pytest
from glucotrust.corpus import Passage


@pytest.fixture
def passage():
    return Passage(passage_id="q1#p1", doc_id="doc", qid="q1", source="NIDDK", url="https://example.org/diabetes",
                   focus="Diabetes", qtype="information", question="What is diabetes?",
                   text="Insulin helps glucose enter cells. Diabetes can affect blood glucose.")
