import pandas as pd
import streamlit as st


# ==========================
# DATA LOADING
# ==========================
def load_assignments() -> pd.DataFrame:
    """
    Loads the proofing assignments directly from your Google Sheet.

    Sheet URL:
    https://docs.google.com/spreadsheets/d/1K7N24aqjEkDc4pfVm1ArabInI8jhyCI_mCYujHQbrYc/edit?gid=0#gid=0
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
    roles: list[str],
    proof_stages: list[str],
) -> pd.DataFrame:
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

    if roles:
        filtered = filtered[filtered["Role"].isin(roles)]

    if proof_stages:
        filtered = filtered[filtered["Proof Stage"].isin(proof_stages)]

    return filtered


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
    all_countries = sorted([v for v in df["Country"].unique() if v])
    all_brands = sorted([v for v in df["Brand"].unique() if v])
    all_asset_types = sorted([v for v in df["Asset Type"].unique() if v])
    all_departments = sorted([v for v in df["Department"].unique() if v])
    all_roles = sorted([v for v in df["Role"].unique() if v])
    all_proof_stages = sorted([v for v in df["Proof Stage"].unique() if v])

    countries = st.sidebar.multiselect("Country", options=all_countries)
    brands = st.sidebar.multiselect("Brand", options=all_brands)
    asset_types = st.sidebar.multiselect("Asset Type", options=all_asset_types)
    departments = st.sidebar.multiselect("Department", options=all_departments)
    roles = st.sidebar.multiselect("Role", options=all_roles)
    proof_stages = st.sidebar.multiselect("Proof Stage", options=all_proof_stages)

    # Filter dataframe
    filtered_df = filter_assignments(
        df=df,
        name_search=name_search,
        countries=countries,
        brands=brands,
        asset_types=asset_types,
        departments=departments,
        roles=roles,
        proof_stages=proof_stages,
    )

    st.subheader("Proofing Assignments")

    if filtered_df.empty:
        st.info("No assignments match the selected criteria.")
        return

    # Show Name, Role, Proof Stage as requested
    display_cols = ["Name", "Role", "Proof Stage"]
    display_cols = [c for c in display_cols if c in filtered_df.columns]

    st.dataframe(
        filtered_df[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    # Optional: detailed view for one user
    st.markdown("---")
    st.subheader("Details for a Selected User")

    selected_names = sorted(filtered_df["Name"].unique())
    if selected_names:
        selected_name = st.selectbox("Select a Name", options=selected_names)
        person_rows = filtered_df[filtered_df["Name"] == selected_name]
        st.write(f"All assignments for **{selected_name}**:")
        st.dataframe(
            person_rows.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No users available with the current filters.")


if __name__ == "__main__":
    main()
