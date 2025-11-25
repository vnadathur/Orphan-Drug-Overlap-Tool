"""Coordinate the CDSCO and FDA overlap workflow from load to analysis."""

import argparse
import os
import re
import sys

import pandas as pd

# Add parent directory to path for imports when running from different locations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_cdsco_data, load_fda_data
from date_formatter import standardize_dates
from fuzzy_matcher import DrugMatcher
from matching_config import MatchingThresholds, build_thresholds


def _sanitize_output_tag(tag: str | None, threshold: int) -> str:
    """Return a filesystem-friendly suffix for overlap reports."""
    fallback = str(threshold)
    if not tag:
        return fallback
    
    cleaned = re.sub(r'[^A-Za-z0-9._-]+', '-', tag.strip()).strip('-._')
    return cleaned or fallback


def _build_output_path(base_path: str, threshold: int, output_tag: str | None) -> str:
    """Derive the full path to the overlap report based on the selected threshold."""
    safe_suffix = _sanitize_output_tag(output_tag, threshold)
    filename = f"overlap-{safe_suffix}.csv"
    return os.path.join(base_path, 'output', filename)


def create_overlap_report(matches, output_file: str = 'output/overlap.csv') -> pd.DataFrame | None:
    """Build and persist the overlap report once matches exist.

    Args:
        matches: Iterable of match dictionaries returned by the matcher.
        output_file: Target CSV path for the overlap summary.
    Goal:
        Assemble the essential columns, normalize dates, and write the report.
    Returns:
        pandas.DataFrame when matches are present otherwise None.
    Raises:
        None
    """
    if not matches:
        print("No overlapping drugs found!")
        return None
    
    overlap_df = pd.DataFrame(matches)
    
    overlap_df['CDSCO_Approval_Date_Formatted'] = standardize_dates(overlap_df['cdsco_approval_date'])
    overlap_df['FDA_Marketing_Approval_Date_Formatted'] = standardize_dates(
        overlap_df['fda_marketing_approval_date']
    )
    
    output_df = pd.DataFrame(
        {
            'Drug_Name_CDSCO': overlap_df['cdsco_drug'],
            'Drug_Name_FDA': overlap_df['fda_drug'],
            'Indication_CDSCO': overlap_df['cdsco_indication'],
            'Indication_FDA': overlap_df['fda_indication'],
            'CDSCO_Approval_Date': overlap_df['CDSCO_Approval_Date_Formatted'],
            'FDA_Marketing_Approval_Date': overlap_df['FDA_Marketing_Approval_Date_Formatted'],
            'Match_Score': overlap_df['match_score'],
            'FDA_Generic_Name': overlap_df['fda_generic'],
            'FDA_Trade_Name': overlap_df['fda_trade'],
            'FDA_Sponsor_Company': overlap_df['fda_sponsor_company'],
            'FDA_Sponsor_State': overlap_df['fda_sponsor_state'],
            'FDA_Sponsor_Country': overlap_df['fda_sponsor_country']
        }
    ).sort_values('Match_Score', ascending=False)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    output_df.to_csv(output_file, index=False, encoding='utf-8')
    
    return output_df


def _expand_threshold_shorthand(argv: list[str]) -> list[str]:
    """Allow CLI usage like `--90` to stand in for `--threshold 90`."""
    expanded: list[str] = []
    for arg in argv:
        if arg.startswith("--") and arg[2:].isdigit():
            expanded.extend(["--threshold", arg[2:]])
        elif arg.isdigit():
            expanded.extend(["--threshold", arg])
        else:
            expanded.append(arg)
    return expanded


def analyze_matches(overlap_df: pd.DataFrame, thresholds: MatchingThresholds) -> None:
    """Summarize overlap quality for rapid manual review.

    Args:
        overlap_df: DataFrame created by `create_overlap_report`.
    Goal:
        Highlight volumes, confidence bands, and potential mismatches to guide analysts.
    Returns:
        None
    Raises:
        None
    """
    print("\n=== OVERLAP ANALYSIS ===")
    print(f"Total overlapping drugs found: {len(overlap_df)}")
    
    high_floor = thresholds.high_gate
    medium_floor = thresholds.base
    
    high_confidence = len(overlap_df[overlap_df['Match_Score'] >= high_floor])
    medium_confidence = len(
        overlap_df[
            (overlap_df['Match_Score'] >= medium_floor)
            & (overlap_df['Match_Score'] < high_floor)
        ]
    )
    
    print(
        f"\nConfidence breakdown:\n"
        f"  High confidence (≥{high_floor}%): {high_confidence}\n"
        f"  Medium confidence ({medium_floor}-{max(high_floor - 1, medium_floor)}%): {medium_confidence}"
    )
    
    print("\nTop 10 matches:")
    for idx, row in overlap_df.head(10).iterrows():
        print(f"  {row['Drug_Name_CDSCO']} <-> {row['Drug_Name_FDA']} (Score: {row['Match_Score']}%)")
    
    print("\nPotential issues to review:")
    
    overlap_df['indication_length_diff'] = abs(
        overlap_df['Indication_CDSCO'].str.len() - overlap_df['Indication_FDA'].str.len()
    )

    large_diff = overlap_df[overlap_df['indication_length_diff'] > 200]
    if len(large_diff) > 0:
        print(f"  - {len(large_diff)} matches have very different indication lengths (review for false positives)")
    
    missing_cdsco_dates = overlap_df[overlap_df['CDSCO_Approval_Date'] == ''].shape[0]
    missing_fda_dates = overlap_df[overlap_df['FDA_Marketing_Approval_Date'] == ''].shape[0]
    
    if missing_cdsco_dates > 0:
        print(f"  - {missing_cdsco_dates} CDSCO drugs missing approval dates")
    if missing_fda_dates > 0:
        print(f"  - {missing_fda_dates} FDA drugs missing approval dates")


def run_pipeline(threshold: int = 85, output_tag: str | None = None) -> bool:
    """Execute loading, matching, reporting, and analytics in sequence.

    Args:
        threshold: Minimum similarity score used by the matcher.
    Goal:
        Produce the overlap report and print diagnostic summaries in one sweep.
    Returns:
        bool indicating overall success.
    Raises:
        None
    """
    banner = r"""
  ___  ____  ____  _   _    _    _   _   ____  ____  _   _  ____ 
 / _ \|  _ \|  _ \| | | |  / \  | \ | | |  _ \|  _ \| | | |/ ___|
| | | | |_) | |_) | |_| | / _ \ |  \| | | | | | |_) | | | | |  _ 
| |_| |  _ <|  __/|  _  |/ ___ \| |\  | | |_| |  _ <| |_| | |_| |
 \___/|_| \_\_|   |_| |_/_/   \_\_| \_| |____/|_| \_\\___/ \____|
                                                                 
    _    ____ ____ _____ ____ ____    ___ _   _   ___ _   _ ____ ___    _    
   / \  / ___/ ___| ____/ ___/ ___|  |_ _| \ | | |_ _| \ | |  _ \_ _|  / \   
  / _ \| |  | |   |  _| \___ \___ \   | ||  \| |  | ||  \| | | | | |  / _ \  
 / ___ \ |__| |___| |___ ___) |__) |  | || |\  |  | || |\  | |_| | | / ___ \ 
/_/   \_\____\____|_____|____/____/  |___|_| \_| |___|_| \_|____/___/_/   \_\
                                                                             
 +--------------------------------------------------------------------------+
 |                       By: Vikram Nadathur                                |
 +--------------------------------------------------------------------------+
"""
    print(banner)
    print(f"Matching threshold: {threshold}%")
    
    print("\nStep 1: Loading data...")
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cdsco_path = os.path.join(base_path, 'data', 'cdsco.csv')
        fda_path = os.path.join(base_path, 'data', 'FDA.csv')
        report_path = _build_output_path(base_path, threshold, output_tag)
        
        cdsco_df = load_cdsco_data(cdsco_path)
        fda_df = load_fda_data(fda_path)
        print(
            f"  Loaded {len(cdsco_df)} CDSCO drugs\n"
            f"  Loaded {len(fda_df)} FDA orphan drugs"
        )
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return False
    
    print("\nStep 2: Finding overlaps...")
    thresholds = build_thresholds(threshold)
    matcher = DrugMatcher(threshold=thresholds.base, thresholds=thresholds)
    matches = matcher.find_overlaps(cdsco_df, fda_df)
    print(f"  Found {len(matches)} potential matches")
    
    if not matches:
        print("\nNo overlapping drugs found with current threshold.")
        print("Consider lowering the threshold or checking data formats.")
        return False
    
    print("\nStep 3: Creating overlap report...")
    overlap_df = create_overlap_report(matches, output_file=report_path)
    
    if overlap_df is not None:
        print(f"  Report saved to: {report_path}")
        
        analyze_matches(overlap_df, thresholds)
    
    return True


def main(argv: list[str] | None = None):
    """Parse CLI arguments then execute the pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the Orphan Drug overlap analysis pipeline."
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        default=85,
        help="Overall fuzzy match threshold (0-100). Default: 85",
    )
    parser.add_argument(
        "-o",
        "--output-tag",
        type=str,
        default=None,
        help="Optional suffix for the overlap CSV (defaults to the threshold).",
    )
    
    raw_args = argv if argv is not None else sys.argv[1:]
    normalized_args = _expand_threshold_shorthand(list(raw_args))
    args = parser.parse_args(normalized_args)
    
    if args.threshold < 0 or args.threshold > 100:
        parser.error("threshold must be between 0 and 100")
    
    success = run_pipeline(threshold=args.threshold, output_tag=args.output_tag)
    
    if not success:
        sys.exit(1)
    
    print("\n=== PIPELINE COMPLETE ===")
    print("Review the generated overlap CSV inside the output directory.")
    print("\nTo adjust results:")
    print("  - Increase the threshold for fewer, more accurate matches")
    print("  - Decrease the threshold for broader coverage (may include false positives)")
    print(f"\nExample: python {sys.argv[0]} --threshold 90 --output-tag pilot")


if __name__ == "__main__":
    main()