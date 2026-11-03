# Retrieval comparison

| Method | Subset | Recall@3 |
|---|---|---|
| bm25 | overall | 8/15 (53.3%) |
| bm25 | paraphrased | 2/8 (25.0%) |
| dense | overall | 11/15 (73.3%) |
| dense | paraphrased | 4/8 (50.0%) |

## Disagreements

- rq-01: What causes type 1 diabetes? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-02: What are the symptoms of diabetic kidney disease? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-03: What is prediabetes? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-04: What causes type 2 diabetes? BM25 hit: False; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-05: What is peripheral neuropathy? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-06: What is autonomic neuropathy? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-07: What are the treatments for diabetic kidney failure? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-08: Can children develop the form of diabetes usually associated with adults? BM25 hit: False; dense hit: False. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-09: Can damage to the renal system from high blood sugar be silent at first? BM25 hit: False; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-10: Why does the body's defense system destroy the cells that make insulin? BM25 hit: True; dense hit: False. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-11: How can diabetes damage nerves and cause loss of feeling in the limbs? BM25 hit: False; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-12: Where are the body's two urine-filtering organs situated? BM25 hit: True; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-13: Can losing a little weight and moving more delay the onset of high blood sugar disease? BM25 hit: False; dense hit: True. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-14: What happens when the body's tissues stop responding properly to the hormone that moves sugar into cells? BM25 hit: False; dense hit: False. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
- rq-15: Can nerve injury interfere with digestion and regulation of arterial pressure? BM25 hit: False; dense hit: False. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.
