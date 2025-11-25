# Installation

Follow the steps below to set up the Orphan Drug Overlap Tool locally, install dependencies, and learn about the CLI flags now available for experimentation.

## Prerequisites

- Python 3.10+ (the project was last tested with the UV global virtual environment referenced in the README).
- Access to the CDSCO and FDA CSVs stored under `data/`.
- Optional but recommended: a virtual environment (e.g., `python -m venv .venv` or the provided `$HOME/Documents/uv_global_venv`).

## Environment Setup

```bash
cd /path/to/Orphan-Drug-Overlap-Tool
source "$HOME/Documents/uv_global_venv/bin/activate"  # or your own venv
pip install -r requirements.txt
```

The `pip install` step brings in the runtime dependencies required by the pipeline (`pandas` for data wrangling and `rapidfuzz` for similarity scoring).

## Running the Pipeline

### Shortcut wrapper

```bash
python run_pipeline.py [flags]
```

### Direct entry point

```bash
python pipeline/run_analysis.py [flags]
```

Both commands accept the same arguments because `run_pipeline.py` simply forwards all parameters to the pipeline module.

## Available CLI Flags

| Flag | Description | Default |
| --- | --- | --- |
| `-t, --threshold` | Overall fuzzy match threshold applied across all candidates (0-100). Lowering this value increases recall and risk of false positives. | `85` |
| `-o, --output-tag` | Optional suffix appended to the generated CSV name (e.g., `--output-tag pilot` produces `output/overlap-pilot.csv`). When omitted, the threshold value is used (e.g., `overlap-75.csv`). | `None` |

### Examples

```bash
# Run with default threshold (85%) and output file output/overlap-85.csv
python run_pipeline.py

# More conservative overlap set with explicit suffix
python run_pipeline.py --threshold 92 --output-tag q1-review

# Aggressive search with lower threshold and default suffix (overlap-75.csv)
python run_pipeline.py -t 75
```

After execution, the overlap CSV lives under `output/` and the console summarizes match confidence tiers plus indication-length discrepancies to review. Subsequent sections of the documentation will describe the data inputs, overlap interpretation, and analytics tooling in detail.
