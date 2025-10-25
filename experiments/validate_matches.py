#!/usr/bin/env python3
"""Validate overlap matches and flag likely false positives for review."""

import os
import sys
from datetime import datetime

import pandas as pd
# Add pipeline directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pipeline'))


class OptimizedMatchValidator:
    """Provides classify_match, generate_validation_report, helper predicates."""
    
    def __init__(self, overlap_path='output/overlap.csv'):
        """Load overlap results and derive baseline statistics.

        Args:
            overlap_path: Relative path pointing to the overlap CSV file.
        Goal:
            Populate the validator with data and precomputed aggregates for later queries.
        Returns:
            None
        """
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.overlap_df = pd.read_csv(os.path.join(self.base_path, overlap_path))
        
        # Pre-compute match statistics for efficiency
        self._compute_statistics()
        
        self.false_positive_patterns = {
            ('urea', 'hydroxyurea'): 'Different drugs despite name similarity',
            ('salicylic acid', 'aminosalicylic acid'): 'Different compounds',
            ('potassium', 'bismuth'): 'Matched on a common ion in unrelated drugs',
            ('ethanol', 'ethanolamine'): 'Ethanol versus ethanolamine oleate',
            ('cipro', 'ofloxacin'): 'Different fluoroquinolones share prefixes',
            ('day', 'daybue'): 'Coincidental substring overlap'
        }
    
    def _compute_statistics(self):
        """Build score distribution bins for fast summary reporting.

        Args:
            None
        Goal:
            Cache counts for the headline score tiers used throughout the validator.
        Returns:
            None
        """
        self.total_matches = len(self.overlap_df)
        score = self.overlap_df['Match_Score']
        self.score_distribution = {
            '100': (score == 100).sum(),
            '95-99': ((score >= 95) & (score < 100)).sum(),
            '90-94': ((score >= 90) & (score < 95)).sum(),
            '85-89': ((score >= 85) & (score < 90)).sum()
        }
    
    def classify_match(self, row):
        """Assign a confidence tier to a single overlap record.

        Args:
            row: Series containing CDSCO and FDA names, match score and indications.
        Goal:
            Blend score-based heuristics with curated patterns to prioritize manual review.
        Returns:
            dict describing confidence, recommendation, rationale and flags.
        """
        score = row['Match_Score']
        cdsco_name = row['Drug_Name_CDSCO'].lower()
        fda_name = row['Drug_Name_FDA'].lower()
        
        classification = {'confidence': 'high', 'flags': [], 'recommendation': 'accept', 'reason': ''}
        
        # Rule 1: Perfect matches (100%) are ALWAYS high confidence
        # This is the key principle - same drug name = valid match
        if score == 100:
            classification['confidence'] = 'high'
            classification['recommendation'] = 'accept'
            classification['reason'] = 'Perfect name match'
            
            # Still flag interesting differences for analysis
            if self._has_indication_mismatch(row):
                classification['flags'].append('Different indications (expected)')
            if self._is_combination_to_single(row):
                classification['flags'].append('Combination matched to component')
                
            return classification
        
        # Rule 2: Check for known false positive patterns
        false_pattern = self._check_false_patterns(cdsco_name, fda_name)
        if false_pattern:
            classification['confidence'] = 'low'
            classification['recommendation'] = 'reject'
            classification['reason'] = false_pattern
            classification['flags'].append('Known false positive pattern')
            return classification
        
        # Rule 3: High scores (95-99) are generally reliable
        if score >= 95:
            classification['confidence'] = 'high'
            classification['recommendation'] = 'accept'
            classification['reason'] = 'Very high similarity score'
            
            # Minor differences acceptable at this level
            if self._has_salt_form_difference(cdsco_name, fda_name):
                classification['flags'].append('Different salt forms')
                
        # Rule 4: Good scores (90-94) need context
        elif score >= 90:
            classification['confidence'] = 'medium'
            classification['recommendation'] = 'review'
            classification['reason'] = 'Good similarity, needs verification'
            
            # Check for specific issues
            if self._is_likely_different_drug(row):
                classification['confidence'] = 'low'
                classification['flags'].append('Possibly different drugs')
                
        # Rule 5: Borderline scores (85-89) are suspicious
        else:
            classification['confidence'] = 'low'
            classification['recommendation'] = 'review'
            classification['reason'] = 'Borderline similarity score'
            
            # These need careful review
            if len(cdsco_name.split()) != len(fda_name.split()):
                classification['flags'].append('Different word counts')
        
        return classification
    
    def _check_false_patterns(self, name1, name2):
        """Detect known false positive name pairings.

        Args:
            name1: Lowercased CDSCO name.
            name2: Lowercased FDA name.
        Goal:
            Flag classic failure modes originating from misleading substrings.
        Returns:
            str describing the pattern when triggered, otherwise None.
        """
        for (pattern1, pattern2), reason in self.false_positive_patterns.items():
            if ((pattern1 in name1 and pattern2 in name2) or 
                (pattern2 in name1 and pattern1 in name2)):
                return reason
        return None
    
    def _has_indication_mismatch(self, row):
        """Highlight large indication discrepancies.

        Args:
            row: Series with indication fields from both datasets.
        Goal:
            Signal divergent therapeutic areas while keeping valid matches intact.
        Returns:
            bool indicating whether indications lack shared medical terms.
        """
        cdsco_ind = str(row.get('Indication_CDSCO', '')).lower()
        fda_ind = str(row.get('Indication_FDA', '')).lower()
        
        if not cdsco_ind or not fda_ind:
            return False
        
        # Simple check: do they share any key medical terms?
        medical_terms = ['cancer', 'diabetes', 'hypertension', 'infection', 
                        'epilepsy', 'arthritis', 'asthma']
        
        cdsco_terms = set(term for term in medical_terms if term in cdsco_ind)
        fda_terms = set(term for term in medical_terms if term in fda_ind)
        
        # Different if no overlap in medical terms
        return len(cdsco_terms) > 0 and len(fda_terms) > 0 and not cdsco_terms.intersection(fda_terms)
    
    def _is_combination_to_single(self, row):
        """Check whether a combination drug paired with a single ingredient.

        Args:
            row: Series describing the match under review.
        Goal:
            Identify cases where the CDSCO entry contains multiple actives yet the FDA entry does not.
        Returns:
            bool indicating the presence of combination markers.
        """
        cdsco_name = row['Drug_Name_CDSCO']
        return any(sep in cdsco_name for sep in [' + ', ' & ', ' with '])
    
    def _has_salt_form_difference(self, name1, name2):
        """Detect simple salt form differences.

        Args:
            name1: Lowercased CDSCO name.
            name2: Lowercased FDA name.
        Goal:
            Catch benign salt variants so reviewers do not discard valid alignments.
        Returns:
            bool indicating whether trimmed bases match while names differ.
        """
        # Common salt forms
        salts = ['hydrochloride', 'hcl', 'sulfate', 'acetate', 'sodium', 
                'potassium', 'calcium', 'mesylate', 'citrate']
        
        # Remove salt forms and compare
        base1 = name1
        base2 = name2
        for salt in salts:
            base1 = base1.replace(salt, '').strip()
            base2 = base2.replace(salt, '').strip()
        
        # If bases are similar, it's just a salt difference
        return base1 == base2 and name1 != name2
    
    def _is_likely_different_drug(self, row):
        """Label medium tier matches that resemble unrelated drugs.

        Args:
            row: Series representing the match under review.
        Goal:
            Guard against confident-looking matches that diverge sharply in indications.
        Returns:
            bool indicating whether the mismatch warrants caution.
        """
        # If indications are completely different therapeutic areas
        if self._has_indication_mismatch(row):
            # And it's not a perfect match
            if row['Match_Score'] < 95:
                return True
        
        return False
    
    def generate_validation_report(self):
        """Produce markdown and CSV outputs summarizing validation status.

        Args:
            None
        Goal:
            Surface low confidence matches, highlight indication differences and store structured data for follow up.
        Returns:
            dict with aggregated counts for quick console summaries.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.base_path, 'experiments', 'results',
                                   f'validation_report_{timestamp}.md')
        
        # Classify all matches
        classifications = []
        indication_differences = []  # Track interesting indication differences
        
        for idx, row in self.overlap_df.iterrows():
            classification = self.classify_match(row)
            classification['index'] = idx
            classification['row'] = row
            classifications.append(classification)
            
            # Track perfect matches with different indications (interesting findings)
            if (classification['confidence'] == 'high' and 
                'Different indications (expected)' in classification['flags']):
                indication_differences.append(row)
        
        # Group by confidence
        high_conf = [c for c in classifications if c['confidence'] == 'high']
        medium_conf = [c for c in classifications if c['confidence'] == 'medium']
        low_conf = [c for c in classifications if c['confidence'] == 'low']
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Drug Match Validation Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n")
            f.write(f"- Total matches analyzed: {self.total_matches}\n")
            f.write(f"- High confidence: {len(high_conf)} ({len(high_conf)/self.total_matches*100:.1f}%)\n")
            f.write(f"- Medium confidence: {len(medium_conf)} ({len(medium_conf)/self.total_matches*100:.1f}%)\n")
            f.write(f"- Low confidence: {len(low_conf)} ({len(low_conf)/self.total_matches*100:.1f}%)\n\n")
            
            # Score distribution
            f.write("## Score Distribution\n")
            for range_name, count in self.score_distribution.items():
                f.write(f"- Score {range_name}: {count} matches\n")
            f.write("\n")
            
            # Priority Review Section
            f.write("## Priority Review: Low Confidence Matches\n")
            f.write("These matches likely contain errors and need manual review:\n\n")
            
            for cls in low_conf:
                row = cls['row']
                f.write(f"### {cls['index'] + 1}. {row['Drug_Name_CDSCO']} ↔ {row['Drug_Name_FDA']}\n")
                f.write(f"- **Score**: {row['Match_Score']:.1f}\n")
                f.write(f"- **Reason**: {cls['reason']}\n")
                f.write(f"- **Flags**: {', '.join(cls['flags']) if cls['flags'] else 'None'}\n")
                cdsco_ind = str(row.get('Indication_CDSCO', 'N/A'))
                fda_ind = str(row.get('Indication_FDA', 'N/A'))
                f.write(f"- **CDSCO Indication**: {cdsco_ind[:150]}{'...' if len(cdsco_ind) > 150 else ''}\n")
                f.write(f"- **FDA Indication**: {fda_ind[:150]}{'...' if len(fda_ind) > 150 else ''}\n")
                f.write(f"- **Action**: [ ] Accept [ ] Reject [ ] Needs Investigation\n\n")
            
            # Interesting Findings Section
            if indication_differences:
                f.write("## Interesting Findings: Same Drug, Different Indications\n")
                f.write("These are valid matches showing how the same drug is used differently:\n\n")
                
                for row in indication_differences[:10]:  # Show first 10
                    f.write(f"### {row['Drug_Name_CDSCO']}\n")
                    cdsco_use = str(row.get('Indication_CDSCO', 'N/A'))
                    fda_use = str(row.get('Indication_FDA', 'N/A'))
                    f.write(f"- **CDSCO Use**: {cdsco_use[:200]}{'...' if len(cdsco_use) > 200 else ''}\n")
                    f.write(f"- **FDA Use**: {fda_use[:200]}{'...' if len(fda_use) > 200 else ''}\n\n")
                
                if len(indication_differences) > 10:
                    f.write(f"*...and {len(indication_differences) - 10} more examples*\n\n")
            
            # Medium confidence section (brief)
            f.write("## Medium Confidence Matches (Brief Summary)\n")
            f.write(f"Total: {len(medium_conf)} matches needing verification\n\n")
            
            # Show a few examples
            for cls in medium_conf[:5]:
                row = cls['row']
                f.write(f"- {row['Drug_Name_CDSCO']} ↔ {row['Drug_Name_FDA']} (Score: {row['Match_Score']:.1f})\n")
            
            if len(medium_conf) > 5:
                f.write(f"- *...and {len(medium_conf) - 5} more*\n")
        
        # Generate CSV for data analysis
        csv_data = []
        for cls in classifications:
            row = cls['row']
            csv_data.append({
                'cdsco_drug': row['Drug_Name_CDSCO'],
                'fda_drug': row['Drug_Name_FDA'],
                'match_score': row['Match_Score'],
                'confidence': cls['confidence'],
                'recommendation': cls['recommendation'],
                'reason': cls['reason'],
                'flags': '|'.join(cls['flags']) if cls['flags'] else '',
                'cdsco_indication': row.get('Indication_CDSCO', ''),
                'fda_indication': row.get('Indication_FDA', '')
            })
        
        csv_df = pd.DataFrame(csv_data)
        csv_path = report_path.replace('.md', '.csv')
        csv_df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"\nValidation complete!")
        print(f"Report saved to: {report_path}")
        print(f"CSV saved to: {csv_path}")
        
        # Return summary statistics
        return {
            'total': self.total_matches,
            'high_confidence': len(high_conf),
            'medium_confidence': len(medium_conf),
            'low_confidence': len(low_conf),
            'estimated_false_positives': len([c for c in low_conf if c['recommendation'] == 'reject']),
            'indication_differences': len(indication_differences)
        }


def main():
    """Execute the validation workflow from load through reporting.

    Args:
        None
    Goal:
        Invoke the validator, generate outputs and emit a console summary.
    Returns:
        None
    """
    print("Starting optimized match validation...")
    
    validator = OptimizedMatchValidator()
    stats = validator.generate_validation_report()
    
    print("\n=== Validation Summary ===")
    print(f"Total matches: {stats['total']}")
    print(f"High confidence: {stats['high_confidence']} ({stats['high_confidence']/stats['total']*100:.1f}%)")
    print(f"Estimated false positives: {stats['estimated_false_positives']}")
    print(f"Same drug, different indications: {stats['indication_differences']}")
    
    print("\nNext steps:")
    print("1. Review low confidence matches in the report")
    print("2. Verify medium confidence matches if needed")
    print("3. Analyze indication differences for research insights")


if __name__ == "__main__":
    main()