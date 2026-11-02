from pathlib import Path

from glucotrust.ingest import chunk_answer, parse_xml, relevant
from glucotrust.corpus import load_corpus, save_corpus


def test_xml_and_filter():
    record = parse_xml(Path("tests/fixtures/sample.xml"))[0]
    assert record["source"] == "NIDDK"
    assert record["qid"] == "fixtures:1-1"
    assert relevant(record["focus"], record["question"])
    assert not relevant("Acromegaly", "What causes acromegaly?")
    assert relevant("Diabetic neuropathies", "What are the symptoms?")


def test_chunks_are_bounded():
    text = "one two three\n\nfour five six\n\n" + "word " * 400
    chunks = chunk_answer(text)
    assert all(len(c.split()) <= 150 for c in chunks)
    assert " ".join(" ".join(chunks).split()) == " ".join(text.split())


def test_corpus_roundtrip(passage, tmp_path):
    path = tmp_path / "passages.jsonl"
    save_corpus([passage], path)
    assert load_corpus(path) == [passage]
