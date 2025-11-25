# Same Drug, Different Indication

[Download CSV](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/same-drug-different-indication.csv)

{{ read_csv('same-drug-different-indication.csv', usecols=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}
