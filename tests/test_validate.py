import pytest
from glucotrust.validate import Assessment, Citation, validate_assessment


@pytest.mark.parametrize("citations", [[], [Citation(passage_id="unknown", quote="Insulin")], [Citation(passage_id="q1#p1", quote="Insulin cures diabetes")], [Citation(passage_id="q1#p1", quote="   ")]])
def test_invalid_downgraded(passage, citations):
    result = validate_assessment(Assessment(verdict="supported", citations=citations, explanation="Original claim"), [passage])
    assert result.verdict == "insufficient"
    assert result.validation_failed
    assert result.explanation != "Original claim"


def test_valid_quote_whitespace(passage):
    result = validate_assessment(Assessment(verdict="contradicted", citations=[Citation(passage_id=passage.passage_id, quote="Insulin helps\n glucose enter cells.")], explanation="Evidence conflicts."), [passage])
    assert result.verdict == "contradicted"
    assert not result.validation_failed
