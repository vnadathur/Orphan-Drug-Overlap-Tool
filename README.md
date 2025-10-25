<div align="center">
  <img src="assets/INDOUSRARE%20LOGO.png" alt="IndoUsRare Logo" width="200"/>
  
  # Orphan Drug Overlap Tool
</div>

---

# Drug Overlap Analysis Pipeline

This project began when we collected two datasets: the U.S. Food and Drug Administration (FDA) orphan drug approvals and the Central Drugs Standard Control Organization (CDSCO) drug database from India. The FDA file arrived structured with approval dates, sponsors, trade names, generic names and therapeutic indications. The CDSCO data was different. It contained over six date formats, misclassified entries, spelling errors, stray characters and widespread column spillover.

We needed to identify drugs approved as orphan therapies in the United States that also appear in India's regulatory records. When indications differ between the two agencies, those drugs become candidates for orphan designation in India. That question required clean data and a matching algorithm capable of handling pharmaceutical naming conventions.

## Dataset Preparation

Team members began manually cleaning the CDSCO drug name column. We produced an intermediate version that removed compound details and partially standardized entries. Running our first prototype matcher on that semi-clean data surfaced 138 overlaps and confirmed that systematic cleaning improves detection accuracy. We refined the normalization logic further and generated the final drug name column. Processing that version through the matcher produced 140 overlaps and outperformed multiple online fuzzy matching tools tested on both raw and partially cleaned inputs.

The pipeline now processes `data/cdsco.csv`, which contains single-agent and combination products, alongside `data/FDA.csv`, which lists generic names, trade names, indications and approval dates for orphan drugs.

## How It Works

`pipeline/data_loader.py` reads both files, normalizes drug names by removing salt forms and parenthetical content, and extracts active ingredients from combination therapies. The shared helper `pipeline/utils.py` provides text cleaning routines that strip whitespace and handle nulls consistently. `pipeline/fuzzy_matcher.py` compares CDSCO entries against FDA records using token-based similarity algorithms. It caches normalized names for speed, recognizes when different salts represent the same molecule, and reports match types such as exact, salt variant or partial combination. `pipeline/date_formatter.py` parses the inconsistent date formats from both sources and outputs MM/DD/YYYY strings. `pipeline/drug_overlap_pipeline.py` coordinates the workflow, writes `output/overlap.csv` and prints diagnostic summaries showing confidence distributions and indication mismatches.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Analysis

Execute the pipeline with the default 85% similarity threshold:

```bash
python pipeline/run_analysis.py
```

Adjust the threshold for stricter or more permissive matching:

```bash
python pipeline/run_analysis.py 90
python pipeline/run_analysis.py 80
```

The root-level `run_pipeline.py` script forwards the optional threshold argument to the same entry point.

## Output

The pipeline generates `output/overlap.csv`, sorted by match score. Each row contains CDSCO and FDA drug names, their respective indications, approval dates, match type and similarity percentage. Console output includes confidence tier counts and flags entries where indications differ substantially. Those flagged pairs warrant manual review because they may represent the same drug used for different purposes across jurisdictions.

Raise the threshold when false positives are costly. Lower it when you want broader coverage and plan to verify matches manually.

## Validation Tools

`experiments/validate_matches.py` classifies results into high, medium and low confidence tiers. It produces markdown and CSV reports listing matches that need verification. `experiments/random_sampling_test.py` samples unmatched CDSCO entries and applies relaxed search heuristics to identify drugs the main matcher may have missed. Reviewing those potential false negatives guides improvements to the normalization and scoring logic.

## Performance Characteristics

Processing the current datasets completes in under a minute on standard hardware. The matcher caches normalized drug names and rejects weak candidates early to maintain speed as record counts grow. The final run identified 140 overlaps with a 100% high-confidence rate and negligible false positives. Adding new data sources requires writing a loader function that returns a dataframe with normalized name columns but does not disturb the existing matching or reporting components.
