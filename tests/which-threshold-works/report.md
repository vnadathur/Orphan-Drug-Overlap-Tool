# Question  
Which threshold keeps recall while avoiding unnecessary loosening?

# Setup  
- Small gold set of five expected positives (exact, salt, combo, variant misspelling) and one negative.  
- Thresholds swept: 75, 85, 90, 95.  
- Matcher uses pipeline defaults with config-derived sub-thresholds.

# Result  
- t=75: precision 1.000, recall 1.000 (all positives kept).  
- t=85: precision 1.000, recall 1.000.  
- t=90: precision 1.000, recall 1.000.  
- t=95: precision 1.000, recall 0.800 (lamivudin misspelling drops).  
- Output: `tests/which-threshold-works/results/threshold_sweep.json`.

# Verdict  
Defaults (85–90) retain all intended positives on this gold set; pushing to 95 trims recall.

# Next essential follow-up  
- Expand the gold set with harder near-misses and additional negatives to observe precision movement below 85.  

