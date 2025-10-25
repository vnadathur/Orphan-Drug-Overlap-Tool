#!/usr/bin/env python3
"""Sample unmatched CDSCO entries to uncover missed FDA overlaps."""

import json
import os
import random
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd  # pyright: ignore[reportMissingImports]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from pipeline.data_loader import (
    load_cdsco_data,
    load_fda_data,
    normalize_drug_name,
    extract_active_ingredients,
)
from pipeline.fuzzy_matcher import DrugMatcher


class OptimizedFalseNegativeDetector:
    """Exposes search_with_strategy, sample_and_analyze, save_results."""
    
    def __init__(self, cdsco_df: pd.DataFrame, fda_df: pd.DataFrame, overlap_df: pd.DataFrame):
        """Prime the detector with pre-loaded data for repeatable sampling runs.

        Args:
            cdsco_df: Canonical CDSCO table including at least drug names and indications.
            fda_df: Canonical FDA table with generic names, trade names and indications.
            overlap_df: Output from the main matcher containing confirmed overlaps.
        Goal:
            Retain shared metadata while preparing reusable indices and helper matchers.
        Returns:
            None
        """
        self.cdsco_df = cdsco_df
        self.fda_df = fda_df
        self.overlap_df = overlap_df
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Create sets for O(1) lookup performance
        self.matched_cdsco_lower = set(overlap_df['Drug_Name_CDSCO'].str.lower())
        self.matched_fda_lower = set(overlap_df['Drug_Name_FDA'].str.lower())

        self.fast_matcher = DrugMatcher(threshold=70)
        self.indication_matcher = DrugMatcher(threshold=60)
        
        # Build optimized search indices
        print("Building optimized search indices...")
        self._build_search_indices()
        
        # Common drug name variations and abbreviations
        # This helps catch matches where naming conventions differ
        self.abbreviations = {
            'hcl': 'hydrochloride',
            'inj': 'injection',
            'tab': 'tablet',
            'cap': 'capsule',
            'susp': 'suspension',
            'sulf': 'sulfate',
            'phos': 'phosphate',
            'acet': 'acetate'
        }
        
        self.medical_patterns = [
            r'\b(cancer|tumor|carcinoma|lymphoma|leukemia|sarcoma)\b',
            r'\b(diabetes|diabetic|insulin|hyperglycemia)\b',
            r'\b(hypertension|blood pressure|antihypertensive)\b',
            r'\b(infection|bacterial|viral|fungal|antibiotic)\b',
            r'\b(epilepsy|seizure|anticonvulsant)\b',
            r'\b(depression|anxiety|antidepressant|psychiatric)\b',
            r'\b(arthritis|rheumat|inflammatory|nsaid)\b',
            r'\b(asthma|copd|bronch|respiratory)\b'
        ]
    
    def _build_search_indices(self):
        """Construct reusable indices that accelerate downstream searches.

        Args:
            None
        Goal:
            Normalize FDA entries, cache token level hints and prepare component lookups.
        Returns:
            None
        """
        # Primary search index with all FDA drug variations
        self.fda_search_index = []
        self.fda_by_first_word = defaultdict(list)
        self.fda_components = defaultdict(list)
        
        for idx, row in self.fda_df.iterrows():
            # Create comprehensive entry
            entry = {
                'index': idx,
                'generic': row.get('Generic Name', ''),
                'trade': row.get('Trade Name', ''),
                'generic_normalized': normalize_drug_name(row.get('Generic Name', '')),
                'trade_normalized': normalize_drug_name(row.get('Trade Name', '')),
                'indication': row.get('Approved Labeled Indication', ''),
                'approval_date': row.get('Marketing Approval Date', '')
            }
            
            # Extract searchable components
            generic_lower = entry['generic'].lower()
            trade_lower = entry['trade'].lower()
            
            # Add to primary index
            self.fda_search_index.append(entry)
            
            # Build first-word index for quick filtering
            for name in (generic_lower, trade_lower):
                if name:
                    first_word = name.split()[0]
                    if len(first_word) > 2:
                        self.fda_by_first_word[first_word].append(idx)
            
            # Extract drug components for combination matching
            components = set()
            if entry['generic_normalized']:
                components.update(extract_active_ingredients(entry['generic']))
            if entry['trade_normalized']:
                components.update(extract_active_ingredients(entry['trade']))

            for component in components:
                if len(component) > 3:  # Skip very short components
                    self.fda_components[component].append(idx)
    
    def generate_smart_variations(self, drug_name: str) -> List[str]:
        """Draft search variations that reflect common clinical naming quirks.

        Args:
            drug_name: CDSCO label being investigated.
        Goal:
            Capture consistent transformations that expose hidden matches without manual tweaking.
        Returns:
            list[str] containing normalized candidates ready for similarity scoring.
        """
        variations = set()
        
        # Always include original and basic normalized form
        variations.add(drug_name.lower())
        variations.add(normalize_drug_name(drug_name))
        
        # Handle parenthetical content intelligently
        if '(' in drug_name:
            no_paren = re.sub(r'\s*\([^)]+\)', '', drug_name).strip()
            variations.update({no_paren.lower(), normalize_drug_name(no_paren)})
            for match in re.findall(r'\(([^)]+)\)', drug_name):
                variations.update({match.lower(), normalize_drug_name(match)})
        
        # Expand common abbreviations
        drug_lower = drug_name.lower()
        for abbrev, full in self.abbreviations.items():
            if abbrev in drug_lower:
                expanded = drug_lower.replace(abbrev, full)
                variations.update({expanded, drug_lower.replace(full, abbrev)})
        
        # Extract components for combination drugs
        components = extract_active_ingredients(drug_name)
        variations.update(components)
        
        # For combination drugs, also try each component with common additions
        if len(components) > 1:
            for comp in components:
                variations.update({f"{comp} injection", f"{comp} tablet", f"{comp} solution"})
        
        # Handle salt forms more aggressively
        # Remove all salt forms to get base drug
        base_drug = drug_lower
        salt_patterns = [
            r'\s+(hydrochloride|hcl|chloride|sulfate|sulphate|acetate|phosphate|'
            r'citrate|maleate|fumarate|succinate|tartrate|mesylate|besylate|'
            r'tosylate|bromide|iodide|sodium|potassium|calcium)(\s|$)'
        ]
        
        for pattern in salt_patterns:
            base_drug = re.sub(pattern, ' ', base_drug).strip()
        
        if base_drug != drug_lower:
            variations.add(base_drug)
            
            # Try base drug with different common salts
            variations.update(
                f"{base_drug} {salt}" for salt in ['hydrochloride', 'sulfate', 'sodium', 'potassium']
            )
        
        # Extract first significant word (often the main ingredient)
        words = drug_name.split()
        if words:
            first_word = words[0].lower()
            if len(first_word) > 3 and first_word not in ['oral', 'topical', 'injection']:
                variations.add(first_word)
        
        # Remove duplicates and empty strings
        return [v for v in variations if v and len(v) > 2]
    
    def search_with_strategy(self, cdsco_drug: Dict, strategy: str = 'comprehensive') -> List[Dict]:
        """Locate FDA counterparts for a CDSCO record using staged tactics.

        Args:
            cdsco_drug: Row from the CDSCO table under review.
            strategy: Selector for search breadth.
        Goal:
            Provide flexible entry points so analysts pick depth without rewriting logic.
        Returns:
            list[dict] describing candidate matches sorted by relevance.
        """
        drug_name = cdsco_drug['Drug Name']
        indication = cdsco_drug.get('Indication', '')
        variations = self.generate_smart_variations(drug_name)
        
        handlers = {
            'fast': lambda: self._fast_search(variations),
            'component': lambda: self._component_search(drug_name, variations),
            'indication': lambda: self._indication_search(indication, variations)
        }

        if strategy in handlers:
            return handlers[strategy]()

        results = [match for handler in handlers.values() for match in handler()]

        unique = {}
        for result in results:
            key = (result['fda_generic'], result['fda_trade'])
            if key not in unique or result['match_score'] > unique[key]['match_score']:
                unique[key] = result

        return sorted(unique.values(), key=lambda x: x['match_score'], reverse=True)[:10]
    
    def _fast_search(self, variations: List[str]) -> List[Dict]:
        """Score high probability FDA entries with minimal overhead.

        Args:
            variations: Normalized names derived from the CDSCO label.
        Goal:
            Reuse indices to keep the quick sweep responsive.
        Returns:
            list[dict] containing matches that meet the strict threshold.
        """
        candidates = set()
        
        # Use first-word index for quick candidate selection
        for variation in variations:
            first_word = variation.split()[0] if variation.split() else ''
            if first_word in self.fda_by_first_word:
                candidates.update(self.fda_by_first_word[first_word])
        
        # If no candidates from index, fall back to full search
        if not candidates:
            candidates = range(len(self.fda_search_index))
        
        matcher = self.fast_matcher
        results = []
        
        for idx in candidates:
            fda_entry = self.fda_search_index[idx]
            best_score = 0
            best_variation = ''
            
            for variation in variations:
                # Check generic name
                score = matcher.calculate_similarity(variation, fda_entry['generic_normalized'])
                if score > best_score:
                    best_score = score
                    best_variation = variation
                
                # Check trade name
                score = matcher.calculate_similarity(variation, fda_entry['trade_normalized'])
                if score > best_score:
                    best_score = score
                    best_variation = variation
                
                # Early termination on perfect match
                if best_score == 100:
                    break
            
            if best_score >= 70:
                results.append({
                    'fda_generic': fda_entry['generic'],
                    'fda_trade': fda_entry['trade'],
                    'fda_indication': fda_entry['indication'],
                    'match_score': best_score,
                    'matched_variation': best_variation,
                    'strategy': 'fast_search'
                })
        
        return results
    
    def _component_search(self, drug_name: str, variations: List[str]) -> List[Dict]:
        """Match combination drugs by evaluating each component separately.

        Args:
            drug_name: Original CDSCO string.
            variations: Not used directly yet retained for signature parity.
        Goal:
            Surface FDA entries that reference constituent molecules.
        Returns:
            list[dict] summarizing component-driven matches.
        """
        components = extract_active_ingredients(drug_name)
        if len(components) <= 1:
            return []  # Not a combination drug
        
        results = []

        for component in components:
            for idx in self.fda_components.get(component, []):
                fda_entry = self.fda_search_index[idx]
                significance = len(component) / len(drug_name.lower().replace(' ', ''))
                match_score = min(80 + significance * 20, 95)
                results.append({
                    'fda_generic': fda_entry['generic'],
                    'fda_trade': fda_entry['trade'],
                    'fda_indication': fda_entry['indication'],
                    'match_score': match_score,
                    'matched_variation': f"component: {component}",
                    'strategy': 'component_match'
                })

        return results
    
    def _indication_search(self, indication: str, variations: List[str]) -> List[Dict]:
        """Lean on indication similarity when names alone fall short.

        Args:
            indication: CDSCO therapeutic description.
            variations: Candidate name strings for secondary scoring.
        Goal:
            Bridge semantic gaps when nomenclature diverges yet usage aligns.
        Returns:
            list[dict] containing scored possibilities enriched with overlap explanations.
        """
        if not indication or len(indication) < 10:
            return []
        
        indication_lower = indication.lower()
        
        # Extract key medical terms
        key_terms = set()
        for pattern in self.medical_patterns:
            matches = re.findall(pattern, indication_lower)
            key_terms.update(matches)
        
        if not key_terms:
            return []
        
        # Find FDA drugs with similar indications
        results = []
        matcher = self.indication_matcher

        for fda_entry in self.fda_search_index:
            fda_indication = fda_entry.get('indication', '').lower()
            if not fda_indication:
                continue

            fda_key_terms = set().union(*[re.findall(pattern, fda_indication) for pattern in self.medical_patterns])
            overlap = key_terms.intersection(fda_key_terms)
            if not overlap:
                continue

            name_score = max(
                max(
                    matcher.calculate_similarity(variation, fda_entry['generic_normalized']),
                    matcher.calculate_similarity(variation, fda_entry['trade_normalized'])
                )
                for variation in variations[:3]
            ) if variations else 0

            if name_score >= 50:
                overlap_ratio = len(overlap) / len(key_terms)
                indication_score = 60 + overlap_ratio * 30
                final_score = name_score * 0.7 + indication_score * 0.3
                results.append({
                    'fda_generic': fda_entry['generic'],
                    'fda_trade': fda_entry['trade'],
                    'fda_indication': fda_entry['indication'],
                    'match_score': final_score,
                    'matched_variation': f"indication: {', '.join(overlap)}",
                    'strategy': 'indication_match'
                })

        return results
    
    def sample_and_analyze(self, batch_size: int = 30, num_batches: int = 5, random_seed: int = 42) -> List[Dict]:
        """Execute stratified sampling over unmatched CDSCO drugs and audit each batch.

        Args:
            batch_size: Number of entries per batch.
            num_batches: Count of batches to process sequentially.
            random_seed: Deterministic seed for repeatability.
        Goal:
            Produce a compact review set that reflects both single agents and combinations.
        Returns:
            list[dict] summarizing candidate matches and diagnostics.
        """
        # Get unmatched drugs
        unmatched_mask = ~self.cdsco_df['Drug Name'].str.lower().isin(self.matched_cdsco_lower)
        unmatched_df = self.cdsco_df[unmatched_mask].copy()
        
        print(
            f"\nSampling Configuration:\n"
            f"- Total CDSCO drugs: {len(self.cdsco_df)}\n"
            f"- Already matched: {len(self.matched_cdsco_lower)}\n"
            f"- Available for sampling: {len(unmatched_df)}\n"
            f"- Sample size: {num_batches} batches × {batch_size} drugs = {num_batches * batch_size} total"
        )
        
        # Stratify by drug type (single vs combination)
        unmatched_df['is_combination'] = unmatched_df['Drug Name'].str.contains(r'[+&]|with', regex=True)
        
        all_results = []
        random.seed(random_seed)
        
        for batch_num in range(num_batches):
            print(f"\n{'='*50}\nProcessing Batch {batch_num + 1}/{num_batches}\n{'='*50}")
            
            # Stratified sampling: ensure mix of single and combination drugs
            combination_drugs = unmatched_df[unmatched_df['is_combination']]
            single_drugs = unmatched_df[~unmatched_df['is_combination']]
            
            # Sample proportionally
            n_combinations = min(int(batch_size * 0.3), len(combination_drugs))
            n_singles = min(batch_size - n_combinations, len(single_drugs))
            
            batch_sample = pd.concat([
                combination_drugs.sample(n=n_combinations, random_state=random_seed + batch_num),
                single_drugs.sample(n=n_singles, random_state=random_seed + batch_num + 1000)
            ])
            
            batch_results = []
            
            for idx, (_, cdsco_drug) in enumerate(batch_sample.iterrows()):
                drug_name = cdsco_drug['Drug Name']
                print(f"\n[{idx + 1}/{len(batch_sample)}] Analyzing: {drug_name}")
                
                potential_matches = self.search_with_strategy(cdsco_drug, strategy='comprehensive')
                
                if potential_matches:
                    # Limit to top 5 matches
                    top_matches = potential_matches[:5]
                    
                    result = {
                        'batch': batch_num + 1,
                        'cdsco_drug': drug_name,
                        'cdsco_indication': cdsco_drug.get('Indication', ''),
                        'is_combination': cdsco_drug['is_combination'],
                        'potential_matches': top_matches,
                        'best_match': top_matches[0],
                        'num_matches_found': len(potential_matches)
                    }
                    
                    batch_results.append(result)
                    
                    # Print summary
                    best = top_matches[0]
                    print(f"  ✓ Found {len(potential_matches)} potential matches")
                    print(f"  Best: {best['fda_generic']} (Score: {best['match_score']:.1f}, "
                          f"Strategy: {best['strategy']})")
                else:
                    print(f"  ✗ No potential matches found")
            
            all_results.extend(batch_results)
            
            # Batch summary
            print(
                f"\nBatch {batch_num + 1} Summary:\n"
                f"- Drugs analyzed: {len(batch_sample)}\n"
                f"- Potential matches found: {len(batch_results)}\n"
                f"- Success rate: {len(batch_results)/len(batch_sample)*100:.1f}%"
            )
        
        return all_results
    
    def save_results(self, results: List[Dict], output_dir: str = None) -> Tuple[str, str]:
        """Persist sampling outcomes to human readable and machine readable files.

        Args:
            results: List of dictionaries produced by `sample_and_analyze`.
            output_dir: Optional override for the write location.
        Goal:
            Retain audit evidence and enable quick exploration without rerunning the sampler.
        Returns:
            tuple[str, str] containing markdown and CSV paths.
        """
        if output_dir is None:
            output_dir = os.path.join(self.base_path, 'experiments', 'results')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"false_negative_analysis_{timestamp}"
        
        # Save detailed markdown report
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# False Negative Detection Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n")
            f.write(f"- Total potential false negatives: {len(results)}\n")
            f.write(f"- Combination drugs: {sum(1 for r in results if r['is_combination'])}\n")
            f.write(f"- Single drugs: {sum(1 for r in results if not r['is_combination'])}\n\n")
            
            # Strategy breakdown
            strategy_counts = defaultdict(int)
            for result in results:
                strategy_counts[result['best_match']['strategy']] += 1
            
            f.write("## Detection Strategy Breakdown\n")
            for strategy, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {strategy}: {count} matches\n")
            f.write("\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"### {i}. {result['cdsco_drug']}\n")
                f.write(f"**Type**: {'Combination' if result['is_combination'] else 'Single'} drug\n")
                f.write(f"**CDSCO Indication**: {result['cdsco_indication']}\n")
                f.write(f"**Matches Found**: {result['num_matches_found']}\n\n")
                
                f.write("**Top Potential Matches**:\n")
                for j, match in enumerate(result['potential_matches'][:3], 1):
                    f.write(f"\n{j}. **{match['fda_generic']}**")
                    if match['fda_trade']:
                        f.write(f" ({match['fda_trade']})")
                    f.write(f"\n   - Score: {match['match_score']:.1f}\n")
                    f.write(f"   - Strategy: {match['strategy']}\n")
                    f.write(f"   - Matched on: {match['matched_variation']}\n")
                    f.write(f"   - FDA Indication: {match['fda_indication'][:200]}...\n")
                
                f.write("\n**Manual Review**:\n")
                f.write("- [ ] True Match (should have been found)\n")
                f.write("- [ ] False Match (correctly not matched)\n")
                f.write("- [ ] Uncertain (needs more investigation)\n")
                f.write("- Notes: _________________________________________\n")
                f.write("\n---\n\n")
        
        # Save CSV for analysis
        csv_data = []
        for result in results:
            best = result['best_match']
            csv_data.append({
                'batch': result['batch'],
                'cdsco_drug': result['cdsco_drug'],
                'cdsco_indication': result['cdsco_indication'],
                'is_combination': result['is_combination'],
                'num_matches': result['num_matches_found'],
                'best_match_fda_drug': best['fda_generic'],
                'best_match_score': best['match_score'],
                'best_match_strategy': best['strategy'],
                'best_match_variation': best['matched_variation']
            })
        
        csv_path = os.path.join(output_dir, f"{base_name}.csv")
        pd.DataFrame(csv_data).to_csv(csv_path, index=False, encoding='utf-8')

        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(
            "\nResults saved:\n"
            f"- Markdown report: {md_path}\n"
            f"- CSV data: {csv_path}\n"
            f"- JSON data: {json_path}"
        )

        return md_path, csv_path


def main():
    """Run the optimized false negative detection workflow end to end.

    Args:
        None
    Goal:
        Load pipeline data, execute the exploratory sampler and archive findings.
    Returns:
        None
    """
    print("=== Optimized False Negative Detection ===")
    print("Loading data...")
    
    # Load all required data
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cdsco_df = load_cdsco_data(os.path.join(base_path, 'data', 'cdsco.csv'))
    fda_df = load_fda_data(os.path.join(base_path, 'data', 'FDA.csv'))
    overlap_df = pd.read_csv(os.path.join(base_path, 'output', 'overlap.csv'))
    
    # Initialize detector
    detector = OptimizedFalseNegativeDetector(cdsco_df, fda_df, overlap_df)
    
    # Run analysis
    results = detector.sample_and_analyze(batch_size=30, num_batches=5)
    
    # Save results
    md_path, csv_path = detector.save_results(results)
    
    # Final summary
    print("\n=== Analysis Complete ===")
    print(f"Potential false negatives found: {len(results)}")
    print(f"Success rate: {len(results)/(5*30)*100:.1f}%")
    print("\nNext steps:")
    print("1. Review the markdown report for detailed matches")
    print("2. Classify each match as True/False/Uncertain")
    print("3. Use findings to improve the main matching algorithm")


if __name__ == "__main__":
    main()