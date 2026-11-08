import pytest
from glucotrust.corpus import Passage


@pytest.fixture(autouse=True)
def isolate_app_resources(monkeypatch):
    # AppTest sessions share process resources, just as real visitors do. Keep
    # each test's limiter and mocked retriever independent of previous tests.
    import streamlit as st
    import glucotrust.limits as limits
    monkeypatch.setattr(limits, "_app_limiter", None)
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


@pytest.fixture
def passage():
    return Passage(passage_id="q1#p1", doc_id="doc", qid="q1", source="NIDDK", url="https://example.org/diabetes",
                   focus="Diabetes", qtype="information", question="What is diabetes?",
                   text="Insulin helps glucose enter cells. Diabetes can affect blood glucose.")
