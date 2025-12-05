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

    # Make sure these columns exist and fill blanks
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
# FILTERING
# ==========================
def filter_assignments(
    df: pd.DataFrame,
    name_search: str,
    countries: list[str],
    brands: list[str],
    asset_types: list[str],
    departments: list[str],
) -> pd.DataFrame:
    """
    Note: no Role/Proof Stage filters anymore – per your request.
    """
    filtered = df.copy()

    # Name search (case-insensitive, partial)
    if name_search:
        term = name_search.lower()
        filtered = filtered[filtered["Name"].str.lower().str.contains(term)]

    if countries:
        filtered = filtered[filtered["Country"].isin(countries)]

    if brands:
        filtered = filtered[filtered["Brand"].isin(brands)]

    if asset_types:
        filtered = filtered[filtered["Asset Type"].isin(asset_types)]

    if departments:
        filtered = filtered[filtered["Department"].isin(departments)]

    return filtered


# ==========================
# PROOF STAGE SORT HELPER
# ==========================
def add_proof_stage_sort_key(df: pd.DataFrame) -> pd.DataFrame:
    """Add a column with the custom sort order for Proof Stage."""

    order = [
        "WIP",
        "Content Approval",
        "Messaging Approval",
        "Management Approval",
        "Executive Review",
        "Production Approval",
    ]
    order_map = {label.lower(): i for i, label in enumerate(order)}

    def get_stage_rank(stage: str) -> int:
        text = str(stage).lower()
        for label, rank in order_map.items():
            if label in text:
                return rank
        # Anything unknown goes to the bottom
        return len(order)

    df = df.copy()
    df["_proof_stage_rank"] = df["Proof Stage"].apply(get_stage_rank)
    return df


# ==========================
# STREAMLIT APP
# ==========================
def main():
    st.set_page_config(
        page_title="Fusion Proofing Assignments",
        page_icon="📝",
        layout="wide",
    )

    st.title("📝 Fusion Proofing Assignments")

    # Load data from Google Sheets
    df = load_assignments()

    # Sidebar – filters and search
    st.sidebar.header("Filters")

    # Name search
    name_search = st.sidebar.text_input("Search by Name")

    # Build filter options from data
    all_countries = sorted({v.strip() for v in df["Country"].astype(str) if v.strip()})
    all_brands = sorted({v.strip() for v in df["Brand"].astype(str) if v.strip()})

    # ✅ Fix for Asset Type options: strip + drop blanks, handle as strings
    all_asset_types = sorted(
        {v.strip() for v in df["Asset Type"].astype(str) if v.strip()}
    )

    all_departments = sorted(
        {v.strip() for v in df["Department"].astype(str) if v.strip()}
    )

    countries = st.sidebar.multiselect("Country", options=all_countries)
    brands = st.sidebar.multiselect("Brand", options=all_brands)
    asset_types = st.sidebar.multiselect("Asset Type", options=all_asset_types)
    departments = st.sidebar.multiselect("Department", options=all_departments)

    # ❌ Role and Proof Stage dropdowns removed
    # (no sidebar controls or filtering on those fields)

    # Filter dataframe
    filtered_df = filter_assignments(
        df=df,
        name_search=name_search,
        cou
