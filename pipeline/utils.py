"""Shared helpers for cleaning text fields across pipeline modules."""

import pandas as pd


def clean_text_series(series: pd.Series) -> pd.Series:
    """Normalize textual columns to trimmed string values.

    Args:
        series: Pandas Series that may contain mixed types or nulls.
    Goal:
        Provide a consistent string representation before further processing.
    Returns:
        pandas.Series with nulls replaced and whitespace removed.
    Raises:
        None
    """
    return series.fillna('').astype(str).str.strip()


