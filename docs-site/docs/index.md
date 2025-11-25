# Orphan Drug Access in India

CDSCO records are noisy, FDA orphan listings are clean. This tool links them so you can see where access already exists in India and where gaps remain.

## Datasets

| File | Source | Notes |
|------|--------|-------|
| `data/cdsco.csv` | CDSCO portal | Single‑agent and combination products with varied date formats, spelling noise and column spillover |
| `data/FDA.csv` | FDA orphan drug database | Generic and trade names, indications, marketing approval dates, sponsor company and location |

## Pipeline

| Step | Description |
|------|-------------|
| Load | Read both CSVs into pandas and trim whitespace, nulls and obvious data errors |
| Normalize | Remove salt forms and parenthetical text, split combination drugs, cache normalized names |
| Match | Use RapidFuzz token similarity and indication checks to connect CDSCO rows to FDA orphan entries |
| Format | Parse heterogeneous dates to `MM/DD/YYYY` and assemble one overlap table per threshold |

## Running the Analysis

Default run (85 percent threshold):

```bash
python run_pipeline.py
```

Custom threshold:

```bash
python run_pipeline.py -t 90
python run_pipeline.py -t 80
```

Each run writes `output/overlap-<threshold>.csv`, sorted by match score.

## Interpreting Results

- Higher thresholds reduce false positives and shrink the overlap list  
- Lower thresholds surface more candidates and require manual review  
- Rows with very different indications flag drugs that may deserve Indian orphan status

## Validation and Performance

Prototype tests on progressively cleaned CDSCO data produced 140 stable overlaps and outperformed common online fuzzy matchers. The matcher rejects weak candidates early and caches normalized strings so a full run finishes in well under a minute on current datasets. Future sources can plug in through new loader functions without changing the core matching logic.
