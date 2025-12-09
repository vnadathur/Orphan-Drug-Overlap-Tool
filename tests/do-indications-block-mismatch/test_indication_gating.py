"""Ensure divergent indications block matches when name similarity is only moderate."""

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
    records = [
        {
            "Drug Name": "pembrolisumab",  # misspelled to lower match score
            "Indication": "seasonal allergic rhinitis",
            "Date of Approval": "01/01/2020",
        }
    ]
    return pd.DataFrame(records)


def build_fda_frame() -> pd.DataFrame:
    records = [
        {
            "Generic Name": "pembrolizumab",
            "Trade Name": "Keytruda",
            "Approved Labeled Indication": "metastatic melanoma",
            "Marketing Approval Date": "09/04/2014",
            "Sponsor Company": "Merck",
            "Sponsor State": "New Jersey",
            "Sponsor Country": "United States",
        }
    ]
    df = pd.DataFrame(records)
    df["Generic Name_normalized"] = df["Generic Name"].apply(normalize_drug_name)
    df["Trade Name_normalized"] = df["Trade Name"].apply(normalize_drug_name)
    return df


def run_test(threshold: int = 85) -> dict:
    thresholds = build_thresholds(threshold)
    matcher = DrugMatcher(threshold=thresholds.base, thresholds=thresholds)
    cdsco_df = build_cdsco_frame()
    fda_df = build_fda_frame()
    matches = matcher.find_overlaps(cdsco_df, fda_df)

    return {
        "threshold": threshold,
        "matches_found": len(matches),
        "matches": matches,
    }


def write_results(results: dict) -> None:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "indication_gate.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    summary = run_test()
    write_results(summary)
    print(f"Matches found: {summary['matches_found']}")
    if summary["matches_found"] > 0:
        print("Unexpected match passed indication gate.")

