# Installation

## 1. Requirements

- Python 3.10 or newer
- `pip` available on your path

Check:

```bash
python --version
pip --version
```

## 2. Create a virtual environment

From the project root:

```bash
cd Orphan-Drug-Overlap-Tool
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

You can use `uv` instead of `pip` if you prefer a faster resolver:

```bash
uv pip install -r requirements.txt
```

## 4. Run the pipeline

Wrapper script:

```bash
python run_pipeline.py
```

Direct entry point:

```bash
python pipeline/drug_overlap_pipeline.py
```

## CLI Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `-t, --threshold` | 85 | Match similarity cutoff (0-100) |
| `-o, --output-tag` | threshold value | Custom suffix for output filename |

## Examples

```bash
# Default (85% threshold)
python run_pipeline.py

# Stricter matching
python run_pipeline.py -t 92

# Looser matching with custom tag
python run_pipeline.py -t 75 -o exploratory
```

Output lands in `output/overlap-<tag>.csv`.
