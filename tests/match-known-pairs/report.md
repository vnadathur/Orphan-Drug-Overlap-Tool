# Question  
Do known positive pairs match at the default thresholds while a clear negative stays out?

# Setup  
- CDSCO mini-set: zidovudine (exact), amoxicillin trihydrate (salt variant), atenolol & chlorthalidone (combo), randomnovel (negative).  
- FDA mini-set with aligned entries for the first three plus a placebo distractor.  
- Threshold: 85 (config-derived sub-thresholds).

# Result  
- Matches found: 3 (zidovudine, amoxicillin trihydrate, atenolol & chlorthalidone).  
- Negative (randomnovel) excluded.  
- Output: `tests/match-known-pairs/results/test_output.json`.

# Verdict  
Pass. Default thresholds keep intended positives and reject the unrelated entry on this fixture.

# Next two essential tests  
- Calibrate thresholds on a small hand-labeled gold set to chart precision/recall at 75/85/90/95.  
- Stress indication gating: near-identical drug names but divergent indications should fail unless confidence is very high.  

