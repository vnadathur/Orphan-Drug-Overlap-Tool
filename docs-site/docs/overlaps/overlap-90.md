# 90% Threshold

[Download CSV](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/overlap-90.csv)

{{ read_csv('overlap-90.csv', usecols=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}
