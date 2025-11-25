# Overlap Report – 100% Threshold

**Download:** [overlap-100.csv](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/overlap-100.csv) — includes every column captured by the pipeline for this cutoff.

The table below shows the CDSCO and FDA drug name pairs that cleared the 100% similarity threshold (exact or salt-normalized matches). Use the download link for the full context, including indications, sponsor metadata, dates, and match scores.

{{ read_csv('overlap-100.csv', columns=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}
