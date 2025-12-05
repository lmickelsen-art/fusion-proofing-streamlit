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


def cell_contains_any(value: str, selected: list[str]) -> bool:
    """
    Return True if:
      - no filters selected, OR
      - the cell is blank (acts as a wildcard), OR
      - the comma-separated 'value' contains ANY of the selected tokens.
    """
    # No filters: everyone passes
    if not selected:
        return True

    text = str(value).strip()

    # Blank cell = wildcard (qualifies for any selection)
    if text == "":
        return True

    cell_tokens = [p.strip() for p in text.split(",") if p.strip()]
    return any(s in cell_tokens for s in selected)


# ==========================
# FILTERING
# ==========================
def filter_assignments(
    df: pd.DataFrame,
    countries: list[str],
    brands: list[str],
    asset_types: list[str],
    departments: list[str],
) -> pd.DataFrame:
    filtered = df.copy()

    if countries:
        filtered = filtered[
            filtered["Country"].apply(lambda v: cell_contains_any(v, countries))
        ]

    if brands:
        filtered = filtered[
            filtered["Brand"].apply(lambda v: cell_contains_any(v, brands))
        ]

    if asset_types:
        filtered = filtered[
            filtered["Asset Type"].apply(lambda v: cell_contains_any(v, asset_types))
        ]

    if departments:
        filtered = filtered[
            filtered["Department"].apply(lambda v: cell_contains_any(v, departments))
        ]

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

    # Sidebar – filters (no name search)
    st.sidebar.header("Filters")

    # Build dropdown options from comma-separated data
    all_countries = split_unique_tokens(df["Country"])
    all_brands = split_unique_tokens(df["Brand"])
    all_asset_types = split_unique_tokens(df["Asset Type"])
    all_departments = split_unique_tokens(df["Department"])

    countries = st.sidebar.multiselect("Country", options=all_countries)
    brands = st.sidebar.multiselect("Brand", options=all_brands)
    asset_types = st.sidebar.multiselect("Asset Type", options=all_asset_types)
    departments = st.sidebar.multiselect("Department", options=all_departments)

    # Filter dataframe
    filtered_df = filter_assignments(
        df=df,
        countries=countries,
        brands=brands,
        asset_types=asset_types,
        departments=departments,
    )

    # Apply custom sort order on Proof Stage
    filtered_df = add_proof_stage_sort_key(filtered_df)
    filtered_df = filtered_df.sort_values(
        by=["_proof_stage_rank", "Name"], ascending=[True, True]
    )

    st.subheader("Proofing Assignments")

    if filtered_df.empty:
        st.info("No assignments match the selected criteria.")
        return

    # Show Name, Role, Proof Stage
    display_cols = ["Name", "Role", "Proof Stage"]
    st.dataframe(
        filtered_df[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    # Details for a selected user
    st.markdown("---")
    st.subheader("Details for a Selected User")

    selected_names = sorted(filtered_df["Name"].unique())
    if selected_names:
        selected_name = st.selectbox("Select a Name", options=selected_names)
        person_rows = filtered_df[filtered_df["Name"] == selected_name]
        person_rows = add_proof_stage_sort_key(person_rows).sort_values(
            by=["_proof_stage_rank"], ascending=True
        )
        st.write(f"All assignments for **{selected_name}**:")
        st.dataframe(
            person_rows.drop(columns=["_proof_stage_rank"], errors="ignore")
            .reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No users available with the current filters.")


if __name__ == "__main__":
    main()
