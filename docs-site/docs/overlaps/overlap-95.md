# Overlap Report – 95% Threshold

**Download:** [overlap-95.csv](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/overlap-95.csv) — includes every column captured by the pipeline for this cutoff.

This view captures all CDSCO ↔︎ FDA pairs that scored at least 95%. It contains the 100% matches plus a handful of slightly lower-scoring salt/formulation variants worth manual review.

{{ read_csv('overlap-95.csv', columns=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}

