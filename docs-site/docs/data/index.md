# Data Sources

## CDSCO Dataset

**File:** `data/cdsco.csv`

| Column | Description |
|--------|-------------|
| Drug Name | Active ingredient as listed |
| Indication | Approved therapeutic use in India |
| Approval Date | CDSCO approval timestamp |

## FDA Dataset

**File:** `data/FDA.csv`

| Column | Description |
|--------|-------------|
| Generic Name | Active ingredient |
| Trade Name | Brand name |
| Indication | Orphan designation indication |
| Marketing Approval Date | FDA approval timestamp |
| Sponsor Company | Manufacturer |
| Sponsor State | US state of sponsor |
| Sponsor Country | Country of sponsor |

## Normalization

The pipeline applies these transformations before matching:

- Strip salt suffixes (hydrochloride, mesylate, etc.)
- Remove parenthetical content
- Lowercase and trim whitespace
- Split combination drugs for component matching
