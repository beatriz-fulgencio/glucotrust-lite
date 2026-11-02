import numpy as np
import pytest
from glucotrust.retrieve import BM25Retriever, DenseRetriever


class FakeEncoder:
    def encode(self, texts, **kwargs):
        return np.array([[1., 0.] if "glucose" in text.lower() else [0., 1.] for text in texts])


def test_retrievers_rank_and_invalidate_cache(passage, tmp_path):
    others = [passage.model_copy(update={"passage_id": f"other{i}", "text": f"A description of unrelated topic {i}", "question": "What is sleep?"}) for i in range(3)]
    passages = [passage] + others
    assert BM25Retriever(passages).search("glucose")[0].passage == passage
    dense = DenseRetriever(passages, tmp_path, FakeEncoder())
    assert dense.search("glucose")[0].passage == passage
    DenseRetriever(passages, tmp_path, FakeEncoder())
    assert len(list(tmp_path.glob("*.npz"))) == 1
    DenseRetriever([passage.model_copy(update={"text": "changed glucose content"})] + others, tmp_path, FakeEncoder())
    assert len(list(tmp_path.glob("*.npz"))) == 2
    with pytest.raises(ValueError):
        dense.search("glucose", k=0)
