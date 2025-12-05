import pandas as pd
import streamlit as st


# ==========================
# DATA LOADING
# ==========================
def load_assignments() -> pd.DataFrame:
    """
    Loads the proofing assignments directly from your Google Sheet.
    """

    csv_url = (
        "https://docs.google.com/spreadsheets/d/"
        "1K7N24aqjEkDc4pfVm1ArabInI8jhyCI_mCYujHQbrYc/"
        "export?format=csv&gid=0"
    )

    df = pd.read_csv(csv_url)

    # Clean up column names just in case
    df.columns = [c.strip() for c in df.columns]

    # Ensure required columns and fill blanks
    required_cols = [
        "Name",
        "Country",
        "Brand",
        "Asset Type",
        "Department",
        "Role",
        "Proof Stage",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in data: {missing}")

    df = df.fillna("")

    return df


# ==========================
# HELPERS
# ==========================
def split_unique_tokens(series: pd.Series) -> list[str]:
    """
    Take a column that may contain comma-separated values and return
    a sorted list of unique, trimmed tokens.
    """
    tokens = set()
    for val in series.astype(str):
        for part in val.split(","):
            part = part.strip()
            if part:
                tokens.add(part)
    return sorted(tokens)


def match_country(value: str, selected: list[str]) -> bool:
    """
    Country is REQUIRED when filters are set.

    Rules:
      - If no countries selected -> True
      - If cell is blank and filter has values -> False (must have explicit rule)
      - Otherwise -> True if any selected country is in the cell list
    """
    if not selected:
        return True

    text = str(value).strip()
    if text == "":
        return False  # cannot match if no country rule

    tokens = [t.strip() for t in text.split(",") if t.strip()]
    return any(s in tokens for s in selected)


def match_optional(value: str, selected: list[str]) -> bool:
    """
    Brand, Asset Type, Department are OPTIONAL narrowing filters.

    Rules:
      - If no filters selected -> True
      - If cell is blank -> wildcard (qualifies for any selection)
      - Otherwise -> True if any selected token is in the cell list
    """
    if not selected:
        return True

    text = str(value).strip()
    if text == "":
        # Blank cell = wildcard; does not disqualify this person
        return True

    tokens = [t.strip() for t in text.split(",") if t.strip()]
    return any(s in tokens for s in selected)


# ==========================
# FILTERING
# ==========================
def filter_assignments(
    df: pd.DataFrame,
    countries: list[str],
    brands: list[str],
    asset_type: str | None,
    departments: list[str],
) -> pd.DataFrame:
    """
    Apply the assignment rules:
