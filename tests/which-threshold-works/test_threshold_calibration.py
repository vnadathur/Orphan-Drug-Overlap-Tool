"""Calibrate precision/recall across thresholds on a tiny gold set."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Set

import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "pipeline"))

from data_loader import normalize_drug_name  # noqa: E402
from fuzzy_matcher import DrugMatcher  # noqa: E402
from matching_config import build_thresholds  # noqa: E402


def build_cdsco_frame() -> pd.DataFrame:
    records = [
        {"Drug Name": "zidovudine", "Indication": "HIV treatment", "Date of Approval": "01/04/1988"},
        {"Drug Name": "amoxicillin trihydrate", "Indication": "Bacterial infection", "Date of Approval": "02/02/2000"},
        {"Drug Name": "atenolol & chlorthalidone", "Indication": "Hypertension combo", "Date of Approval": "04/04/2002"},
        {"Drug Name": "abacavir sulfate", "Indication": "HIV", "Date of Approval": "05/05/2003"},
        {"Drug Name": "lamivudin", "Indication": "HIV", "Date of Approval": "06/06/2004"},
        {"Drug Name": "randomnovel", "Indication": "Pain", "Date of Approval": "03/03/2001"},
    ]
    return pd.DataFrame(records)


def build_fda_frame() -> pd.DataFrame:
    records = [
        {"Generic Name": "zidovudine", "Trade Name": "Retrovir", "Approved Labeled Indication": "HIV treatment"},
        {"Generic Name": "amoxicillin", "Trade Name": "Amoxil", "Approved Labeled Indication": "Bacterial infection"},
        {"Generic Name": "atenolol and chlorthalidone", "Trade Name": "Tenoretic", "Approved Labeled Indication": "Hypertension combo"},
        {"Generic Name": "abacavir", "Trade Name": "Ziagen", "Approved Labeled Indication": "HIV"},
        {"Generic Name": "lamivudine", "Trade Name": "Epivir", "Approved Labeled Indication": "HIV"},
    ]
    df = pd.DataFrame(records)
    df["Generic Name_normalized"] = df["Generic Name"].apply(normalize_drug_name)
    df["Trade Name_normalized"] = df["Trade Name"].apply(normalize_drug_name)
    df["Approved Labeled Indication"] = df["Approved Labeled Indication"].fillna("")
    return df


GOLD_POSITIVES = {"zidovudine", "amoxicillin trihydrate", "atenolol & chlorthalidone", "abacavir sulfate", "lamivudin"}


def evaluate(threshold: int) -> dict:
    thresholds = build_thresholds(threshold)
    matcher = DrugMatcher(threshold=thresholds.base, thresholds=thresholds)
    cdsco_df = build_cdsco_frame()
    fda_df = build_fda_frame()
    matches = matcher.find_overlaps(cdsco_df, fda_df)
    predicted: Set[str] = {m["cdsco_drug"] for m in matches}

    tp = len(predicted & GOLD_POSITIVES)
    fp = len(predicted - GOLD_POSITIVES)
    fn = len(GOLD_POSITIVES - predicted)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "predicted": sorted(predicted),
    }


def run_sweep(thresholds: Iterable[int]) -> list[dict]:
    return [evaluate(t) for t in thresholds]


def write_results(results: list[dict]) -> None:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "threshold_sweep.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    sweep = run_sweep([75, 85, 90, 95])
    write_results(sweep)
    for row in sweep:
        print(
            f"t={row['threshold']}: precision={row['precision']:.3f} "
            f"recall={row['recall']:.3f} predicted={row['predicted']}"
        )

