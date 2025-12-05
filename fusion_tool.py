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


def match_constrained(value: str, selected: list[str]) -> bool:
    """
    Generic matching for Country, Brand, Asset Type, Department.

    Rules per field:
      - If the person's cell is BLANK -> wildcard, always True (no constraint).
      - If the person's cell has values AND filter is selected:
            -> must intersect with selected.
      - If the person's cell has values AND filter is NOT selected:
            -> False (they are constrained but request didn't specify it).
    """
    text = str(value).strip()

    # Person has no constraint for this field → wildcard
    if text == "":
        return True

    tokens = [t.strip() for t in text.split(",") if t.strip()]

    # Person is constrained, but no filter set → do NOT match
    if not selected:
        return False

    # Both sides have values → must intersect
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
    Apply the assignment rules to all 4 dimensions:

      - Country, Brand, Asset Type, Department:
          * If person cell is blank -> wildcard (always ok).
          * If person cell has values:
                - If filter selected -> must match at least one.
                - If filter NOT selected -> person does NOT match.
    """
    filtered = df.copy()

    # Country
    filtered = filtered[
        filtered["Country"].apply(lambda v: match_constrained(v, countries))
    ]

    # Brand
    filtered = filtered[
        filtered["Brand"].apply(lambda v: match_constrained(v, brands))
    ]

    # Asset Type (single select)
    selected_asset_list = [asset_type] if asset_type else []
    filtered = filtered[
        filtered["Asset Type"].apply(lambda v: match_constrained(v, selected_asset_list))
    ]

    # Department
    filtered = filtered[
        filtered["Department"].apply(lambda v: match_constrained(v, departments))
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

    # Sidebar – filters
    st.sidebar.header("Filters")

    all_countries = split_unique_tokens(df["Country"])
    all_brands = split_unique_tokens(df["Brand"])
    all_asset_types = split_unique_tokens(df["Asset Type"])
    all_departments = split_unique_tokens(df["Department"])

    countries = st.sidebar.multiselect("Country", options=all_countries)
    brands = st.sidebar.multiselect("Brand", options=all_brands)

    # Asset Type: single select, optional
    asset_type = st.sidebar.selectbox(
        "Asset Type",
        options=all_asset_types,
        index=None,
        placeholder="Single Select",
    )

    departments = st.sidebar.multiselect("Department", options=all_departments)

    # ---------- Main filtered assignments table ----------
    filtered_df = filter_assignments(
        df=df,
        countries=countries,
        brands=brands,
        asset_type=asset_type,
        departments=departments,
    )

    filtered_df = add_proof_stage_sort_key(filtered_df)
    filtered_df = filtered_df.sort_values(
        by=["_proof_stage_rank", "Name"], ascending=[True, True]
    )

    st.subheader("Proofing Assignments")

    if filtered_df.empty:
        st.info("No assignments match the selected criteria.")
    else:
        display_cols = ["Name", "Role", "Proof Stage"]
        st.dataframe(
            filtered_df[display_cols].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    # ---------- Details for a selected user (IGNORES FILTERS) ----------
    st.markdown("---")
    st.subheader("Details for a Selected User")

    # Use ALL users from the full dataset, not the filtered ones
    all_names = sorted(df["Name"].unique())

    if all_names:
        # selectbox supports type-ahead: as you type, options narrow
        selected_name = st.selectbox("Select a Name", options=all_names)

        person_rows = df[df["Name"] == selected_name]
        person_rows = add_proof_stage_sort_key(person_rows).sort_values(
            by=["_proof_stage_rank"], ascending=True
        )

        st.markdown(f"Assignments for **{selected_name}**:")

        bullet_lines = []
        for _, row in person_rows.iterrows():
            bullet_lines.append(f"- **Country:** {row['Country']}")
            bullet_lines.append(f"- **Brand:** {row['Brand']}")
            bullet_lines.append(f"- **Asset Type:** {row['Asset Type']}")
            bullet_lines.append(f"- **Department:** {row['Department']}")
            bullet_lines.append(f"- **Proof Stage:** {row['Proof Stage']}")
            bullet_lines.append(f"- **Role:** {row['Role']}")
            bullet_lines.append("")  # blank line between assignment blocks

        if bullet_lines:
            st.markdown("\n".join(bullet_lines))
        else:
            st.info("No assignments found for this user.")
    else:
        st.info("No users available in the data.")


if __name__ == "__main__":
    main()
