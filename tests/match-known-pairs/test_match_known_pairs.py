"""Sanity check: do known overlaps match at default thresholds while near-misses stay out."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "pipeline"))

from data_loader import normalize_drug_name  # noqa: E402
from fuzzy_matcher import DrugMatcher  # noqa: E402
from matching_config import build_thresholds  # noqa: E402


def build_cdsco_frame() -> pd.DataFrame:
    """Minimal CDSCO-like frame with positive, salt-variant, combo, and negative cases."""
    records = [
        {
            "Drug Name": "zidovudine",
            "Indication": "HIV treatment",
            "Date of Approval": "01/04/1988",
        },
        {
            "Drug Name": "amoxicillin trihydrate",
            "Indication": "Bacterial infection",
            "Date of Approval": "02/02/2000",
        },
        {
            "Drug Name": "atenolol & chlorthalidone",
            "Indication": "Hypertension combination",
            "Date of Approval": "04/04/2002",
        },
        {
            "Drug Name": "randomnovel",
            "Indication": "Pain",
            "Date of Approval": "03/03/2001",
        },
    ]
    return pd.DataFrame(records)


def build_fda_frame() -> pd.DataFrame:
    """Minimal FDA-like frame with matching and distractor entries."""
    records = [
        {
            "Generic Name": "zidovudine",
            "Trade Name": "Retrovir",
            "Approved Labeled Indication": "HIV treatment",
            "Marketing Approval Date": "03/19/1987",
            "Sponsor Company": "Glaxo Wellcome Inc.",
            "Sponsor State": "North Carolina",
            "Sponsor Country": "United States",
        },
        {
            "Generic Name": "amoxicillin",
            "Trade Name": "Amoxil",
            "Approved Labeled Indication": "Bacterial infection",
            "Marketing Approval Date": "05/05/1999",
            "Sponsor Company": "Beecham",
            "Sponsor State": "New Jersey",
            "Sponsor Country": "United States",
        },
        {
            "Generic Name": "atenolol and chlorthalidone",
            "Trade Name": "Tenoretic",
            "Approved Labeled Indication": "Hypertension combination",
            "Marketing Approval Date": "06/06/1998",
            "Sponsor Company": "AstraZeneca",
            "Sponsor State": "Delaware",
            "Sponsor Country": "United States",
        },
        {
            "Generic Name": "placebo",
            "Trade Name": "Placebox",
            "Approved Labeled Indication": "N/A",
            "Marketing Approval Date": "01/01/2000",
            "Sponsor Company": "None",
            "Sponsor State": "",
            "Sponsor Country": "",
        },
    ]
    df = pd.DataFrame(records)
    df["Generic Name_normalized"] = df["Generic Name"].apply(normalize_drug_name)
    df["Trade Name_normalized"] = df["Trade Name"].apply(normalize_drug_name)
    return df


def run_test() -> dict:
    thresholds = build_thresholds(85)
    matcher = DrugMatcher(threshold=thresholds.base, thresholds=thresholds)

    cdsco_df = build_cdsco_frame()
    fda_df = build_fda_frame()

    matches = matcher.find_overlaps(cdsco_df, fda_df)

    return {
        "threshold": thresholds.base,
        "matches_found": len(matches),
        "match_names": sorted({m["cdsco_drug"] for m in matches}),
        "details": matches,
    }


def write_results(results: dict) -> None:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "test_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    summary = run_test()
    write_results(summary)
    print(f"Matches found: {summary['matches_found']}")
    print("Matched CDSCO drugs:", ", ".join(summary["match_names"]))

