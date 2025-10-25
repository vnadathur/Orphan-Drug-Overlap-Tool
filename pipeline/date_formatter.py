"""Parse and standardize approval dates drawn from drug datasets."""

import re
from datetime import datetime

import pandas as pd

from utils import clean_text_series


def parse_date(date_string: str | None) -> datetime | None:
    """Convert a raw date string into a datetime when possible.

    Args:
        date_string: Original date text from input files.
    Goal:
        Recognize FDA and CDSCO styles while tolerating common separators.
    Returns:
        datetime instance or None when parsing fails.
    Raises:
        None
    """
    if not date_string or pd.isna(date_string) or str(date_string).strip() == '':
        return None
    
    date_str = str(date_string).strip()
    
    formats = [
        '%Y-%m-%d',      # 2017-09-05 (FDA format)
        '%d/%m/%y',      # 3/7/11 (CDSCO format)
        '%d/%m/%Y',      # 03/07/2011
        '%m/%d/%y',      # 7/3/11 (US format variant)
        '%m/%d/%Y',      # 07/03/2011
        '%d-%m-%Y',      # 03-07-2011
        '%d.%m.%Y',      # 03.07.2011
        '%Y/%m/%d',      # 2011/07/03
        '%d-%b-%y',      # 03-Jul-11
        '%d-%b-%Y',      # 03-Jul-2011
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    if '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            try:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                
                if year < 100:
                    if year >= 70:
                        year += 1900
                    else:
                        year += 2000
                
                return datetime(year, month, day)
            except (ValueError, IndexError):
                return None
    
    return None


def format_date_output(date_obj: datetime | None) -> str:
    """Render a datetime as MM/DD/YYYY for reporting.

    Args:
        date_obj: Parsed datetime produced by `parse_date`.
    Goal:
        Provide consistent date strings for exports.
    Returns:
        Formatted string or empty string when parsing failed.
    Raises:
        None
    """
    if not date_obj:
        return ''
    
    return date_obj.strftime('%m/%d/%Y')


def standardize_dates(dates_series: pd.Series) -> pd.Series:
    """Apply parsing and formatting across a Series of raw dates.

    Args:
        dates_series: Pandas Series containing original date strings.
    Goal:
        Deliver a Series with canonical MM/DD/YYYY outputs.
    Returns:
        pandas.Series of formatted strings.
    Raises:
        None
    """
    return clean_text_series(pd.Series(date_str for date_str in dates_series)).apply(
        lambda value: format_date_output(parse_date(value))
    )


if __name__ == "__main__":
    # Test date parsing
    test_dates = [
        '3/7/11',           # CDSCO format
        '2017-09-05',       # FDA format
        '1/1/70',           # Old CDSCO date
        '12/31/2020',       # Full year
        '',                 # Empty
        '15-Jan-21',        # Month name format
        '2021/06/15',       # Alternative format
    ]
    
    print("Testing date parsing and formatting:")
    for date_str in test_dates:
        parsed = parse_date(date_str)
        formatted = format_date_output(parsed)
        print(f"{date_str:15} -> {formatted}")
    
    # Test with pandas Series
    print("\nTesting with pandas Series:")
    dates_series = pd.Series(test_dates)
    standardized = standardize_dates(dates_series)
    for orig, std in zip(test_dates, standardized):
        print(f"{orig:15} -> {std}")