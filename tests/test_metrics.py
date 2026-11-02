import pytest
from glucotrust.metrics import classification_metrics, recall_at_k


def test_hand_computed_matrix_and_denominators():
    metrics = classification_metrics(["supported", "supported", "contradicted", "contradicted", "insufficient", "insufficient"],
                                     ["supported", "insufficient", "supported", "contradicted", "insufficient", None])
    assert metrics["confusion_matrix"] == [[1, 0, 1, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 0, 0]]
    assert metrics["accuracy"]["n"] == 3
    assert metrics["accuracy"]["total"] == 6
    assert metrics["false_support"]["rate"] == .25
    assert metrics["abstention"]["rate"] == .5
    assert metrics["over_abstention"]["rate"] == .25
    assert metrics["availability"]["n"] == 5
    assert metrics["macro_f1"] == pytest.approx((.5 + 2/3 + .5) / 3)
    assert recall_at_k([["a"], [], ["c"]], [["a"], [], ["d"]]) == {"n": 1, "total": 2, "rate": .5}


def test_all_unavailable_not_abstention():
    metrics = classification_metrics(["insufficient"], [None])
    assert metrics["abstention"]["n"] == 0
    assert metrics["macro_f1"] == 0
    assert metrics["available_accuracy"] is None
