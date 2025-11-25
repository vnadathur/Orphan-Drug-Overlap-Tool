# Orphan Drug Overlap Tool

Identifies FDA orphan drugs that also appear in India's CDSCO registry.

## What It Does

- Loads CDSCO and FDA CSV datasets
- Normalizes drug names (salts, combinations, dosage noise)
- Scores matches via RapidFuzz token similarity
- Exports overlap reports at configurable thresholds

## Inputs

| File | Contents |
|------|----------|
| `data/cdsco.csv` | Indian drug approvals from CDSCO portal |
| `data/FDA.csv` | US orphan drug designations with sponsor metadata |

## Outputs

| File | Contents |
|------|----------|
| `output/overlap-<threshold>.csv` | Matched drug pairs with scores, dates, indications |

## Navigation

- **Installation** - Setup, CLI flags
- **Data** - Source schemas
- **Overlaps** - Browse matches by threshold
- **Paper** - Raw tables for publication
