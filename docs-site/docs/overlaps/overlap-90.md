# Overlap Report – 90% Threshold

**Download:** [overlap-90.csv](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/overlap-90.csv)

Lowering the threshold to 90% introduces additional fuzzy matches (e.g., spelling deviations, partial salt overlaps). Review the table and CSV side-by-side to verify which candidates warrant follow-up work.

{{ read_csv('overlap-90.csv', columns=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}

