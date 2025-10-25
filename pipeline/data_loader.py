"""Load and normalize drug datasets for overlap analysis."""

import re

import pandas as pd  # pyright: ignore[reportMissingImports]


def load_cdsco_data(filepath: str = 'data/cdsco.csv') -> pd.DataFrame:
    """Load CDSCO data and prepare core fields.

    Args:
        filepath: Location of the CDSCO CSV.
    Goal:
        Produce a clean frame with normalized drug names and trimmed text fields.
    Returns:
        pandas.DataFrame ready for downstream matching.
    Raises:
        FileNotFoundError when the CSV is unavailable.
    """
    df = pd.read_csv(filepath, encoding='utf-8')
    
    df['Drug Name'] = df['Drug Name'].astype(str).str.strip()
    df['Drug Name_normalized'] = df['Drug Name'].apply(normalize_drug_name)
    
    df['Indication'] = df['Indication'].fillna('').astype(str).str.strip()
    
    df['Date of Approval'] = df['Date of Approval'].astype(str).str.strip()
    
    return df


def load_fda_data(filepath: str = 'data/FDA.csv') -> pd.DataFrame:
    """Load FDA orphan drug data and harmonize naming fields.

    Args:
        filepath: Location of the FDA CSV.
    Goal:
        Return a frame with normalized names and cleaned indications.
    Returns:
        pandas.DataFrame with ready-to-match columns.
    Raises:
        FileNotFoundError when the CSV is unavailable.
    """
    df = pd.read_csv(filepath, encoding='utf-8')
    
    df['Generic Name'] = df['Generic Name'].fillna('').astype(str).str.strip()
    df['Trade Name'] = df['Trade Name'].fillna('').astype(str).str.strip()
    
    df['Generic Name_normalized'] = df['Generic Name'].apply(normalize_drug_name)
    df['Trade Name_normalized'] = df['Trade Name'].apply(normalize_drug_name)
    
    df['Approved Labeled Indication'] = df['Approved Labeled Indication'].fillna('').astype(str).str.strip()
    
    df['Marketing Approval Date'] = df['Marketing Approval Date'].fillna('').astype(str).str.strip()
    
    return df


def normalize_drug_name(drug_name: str) -> str:
    """Standardize a drug name to improve fuzzy matching.

    Args:
        drug_name: Raw name string from source data.
    Goal:
        Remove salt variants, parenthetical clauses, and excess whitespace.
    Returns:
        Normalized lowercase string suitable for similarity checks.
    """
    if not drug_name:
        return ''
    
    normalized = drug_name.lower().strip()
    
    paren_content = re.findall(r'\([^)]+\)', normalized)
    normalized_no_paren = re.sub(r'\s*\([^)]+\)', '', normalized).strip()
    
    salt_forms = [
        r'\s+hydrochloride\b', r'\s+hcl\b', r'\s+chloride\b',
        r'\s+sulfate\b', r'\s+sulphate\b', r'\s+acetate\b',
        r'\s+phosphate\b', r'\s+citrate\b', r'\s+maleate\b',
        r'\s+fumarate\b', r'\s+succinate\b', r'\s+tartrate\b',
        r'\s+mesylate\b', r'\s+besylate\b', r'\s+tosylate\b',
        r'\s+bromide\b', r'\s+iodide\b', r'\s+sodium\b',
        r'\s+potassium\b', r'\s+calcium\b', r'\s+dihydrate\b',
        r'\s+monohydrate\b', r'\s+anhydrous\b'
    ]
    
    for salt in salt_forms:
        normalized_no_paren = re.sub(salt, '', normalized_no_paren, flags=re.IGNORECASE)
    
    normalized_no_paren = re.sub(r'\s+', ' ', normalized_no_paren).strip()
    
    return normalized_no_paren


def extract_active_ingredients(drug_name: str) -> list[str]:
    """Split a combination drug into normalized components.

    Args:
        drug_name: Raw CDSCO drug label.
    Goal:
        Identify each active ingredient for component-based matching.
    Returns:
        list[str] with normalized components or single-entry fallback.
    """
    separators = [' & ', ' + ', ', ', ' with ', ' and ', '/']
    
    drug_lower = drug_name.lower()
    
    components = [drug_lower]
    for sep in separators:
        new_components = []
        for comp in components:
            new_components.extend(comp.split(sep))
        components = new_components
    
    components = [comp.strip() for comp in components if comp.strip()]
    
    if len(components) > 1:
        cleaned = []
        for comp in components:
            comp = re.sub(r'\b\d+\s*(mg|g|mcg|ml|%)\b', '', comp)
            comp = re.sub(r'\b(tablet|capsule|injection|solution)s?\b', '', comp)
            normalized = normalize_drug_name(comp.strip())
            if normalized:
                cleaned.append(normalized)
        return cleaned

    return [normalize_drug_name(drug_lower)]


if __name__ == "__main__":
    # Test loading
    print("Testing data loading...")
    cdsco_df = load_cdsco_data()
    fda_df = load_fda_data()
    
    print(f"Loaded {len(cdsco_df)} CDSCO records")
    print(f"Loaded {len(fda_df)} FDA records")
    
    # Test combination drug extraction
    test_drugs = [
        "atenolol & chlorthalidone",
        "amylobarbitone & trifluoperazine dihydrochloride",
        "single drug name"
    ]
    
    print("\nTesting drug component extraction:")
    for drug in test_drugs:
        components = extract_active_ingredients(drug)
        print(f"{drug} -> {components}")