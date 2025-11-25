# Overlap Report – 80% Threshold

**Download:** [overlap-80.csv](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/overlap-80.csv)

The 80% cut casts a wider net to surface noisier matches—use it when you expect significant spelling or formulation drift between CDSCO and FDA labels.

{{ read_csv('overlap-80.csv', columns=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}

