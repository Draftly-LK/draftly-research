# Dataset release builder

This directory builds local review packages for two planned Hugging Face datasets. It does not create a Hub repository or upload data.

```powershell
python scripts/dataset-release/build_release.py
python scripts/dataset-release/build_release.py --check-urls
python -m unittest discover -s tests -p test_dataset_release.py
python tmp/hf-release/draftly-statutory-retrieval/evaluation/evaluate.py --reference tmp/hf-release/draftly-statutory-retrieval/benchmark_v1/development.jsonl --predictions tmp/hf-release/draftly-statutory-retrieval/evaluation/example-predictions.jsonl
```

The default output is `tmp/hf-release/`, which is ignored by Git. It contains:

- `draftly-statutory-retrieval/`: `benchmark_v1`, `source_papers`, `atomic_question_pool`, lineage, provisional section labels, evaluator, prediction schema and example predictions.
- `draftly-sri-lanka-act-sources/`: 112 paper-corpus Act metadata rows, recorded URLs and unverified registry URL candidates. It contains no PDFs or statutory text.

Each package has a dataset card and a file-hash manifest. `--check-urls` records HTTP reachability and the final URL for the Act index; it does not confirm the linked edition. The team reports question-text redistribution permission. Review the staged rows and the Act link statuses before publishing. The release plan is `research-paper/dataset-release-plan.md`.

Prediction files must have one JSON object per line and cover every question in the selected reference split. The evaluator rejects duplicate IDs and matter splits that leak between development and test.
