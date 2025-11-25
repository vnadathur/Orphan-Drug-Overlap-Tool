# Overlap Report – 85% Threshold

**Download:** [overlap-85.csv](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/overlap-85.csv)

This threshold aligns with the default CLI setting. It strikes a balance between precision and recall, so most analyses start here before ratcheting up/down to test sensitivity.

{{ read_csv('overlap-85.csv', columns=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}

