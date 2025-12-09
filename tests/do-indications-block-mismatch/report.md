# Question  
Do divergent indications block a moderately similar name?

# Setup  
- CDSCO: misspelled “pembrolisumab” with allergic rhinitis indication.  
- FDA: “pembrolizumab” (Keytruda) with metastatic melanoma indication.  
- Threshold: 85 with config-derived sub-thresholds.

# Result  
- Matches found: 0.  
- Output: `tests/do-indications-block-mismatch/results/indication_gate.json`.

# Verdict  
Pass. With moderate name similarity and divergent indications, the gate rejects the pair at default thresholds.

# Next essential follow-up  
- Add a second case: exact-name match but conflicting indications to document when the loose gate allows acceptance (expected with very high name confidence).  

