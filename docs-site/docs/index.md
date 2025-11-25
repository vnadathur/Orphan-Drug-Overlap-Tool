# Orphan Drug Overlap Tool

## Purpose

This project tracks therapies that already earned FDA orphan approval yet also appear in India's CDSCO records. When those listings diverge in indication text, the drugs become immediate candidates for additional advocacy in India. Matching the two datasets required consistent drug names, unified date formats, and transparent reporting so public health teams can review overlaps quickly.

## Data Sources

The pipeline consumes two CSV inputs that live under `data/`. `cdsco.csv` captures small molecules and combinations drawn from the CDSCO portal, while `FDA.csv` lists orphan drugs with sponsor metadata, approval dates, and therapeutic statements. Cleaning focuses on salt removal, parenthetical trimming, and normalization of combination components so the matcher can compare like with like.

## Pipeline Highlights

Data loading standardizes names, resolves dosage noise, and stores helper columns the matcher can reuse. The matcher relies on RapidFuzz scoring, combination-aware logic, and indication cross-checks so clear wins surface to the top of each report. Dates move through the formatter so the overlap CSV always presents MM/DD/YYYY values, and the orchestrator writes one file per threshold to `output/overlap-<tag>.csv`.

## Using These Docs

Use the Installation section when setting up the pipeline or experimenting with thresholds. Visit Data, Overlaps, Analytics, Correspondence, and Paper for deeper dives once you are ready to work with the generated output. Each overlap tab embeds the CDSCO and FDA drug names for its threshold and offers a direct download of the corresponding CSV so you can continue the analysis offline.
