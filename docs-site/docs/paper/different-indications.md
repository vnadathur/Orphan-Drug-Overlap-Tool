# Same Drug, Different Indication

**Download:** [same-drug-different-indication.csv](https://raw.githubusercontent.com/vnadathur/Orphan-Drug-Overlap-Tool/main/output/same-drug-different-indication.csv)

This table lists overlaps where CDSCO and FDA agree on the molecule but describe distinct indications. These candidates often carry the strongest advocacy potential because the active ingredient already appears in both jurisdictions yet targets different patient populations.

{{ read_csv('same-drug-different-indication.csv', columns=['Drug_Name_CDSCO', 'Indication_CDSCO', 'Drug_Name_FDA', 'Indication_FDA']) }}

