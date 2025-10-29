import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fusion Proofing Assignment Tool", layout="wide")

st.title("Fusion Proofing Assignment Tool")

# Load shared Google Sheet as data source
sheet_url = "https://docs.google.com/spreadsheets/d/1K7N24aqjEkDc4pfVm1ArabInI8jhyCI_mCYujHQbrYc/export?format=xlsx"

try:
    data = pd.read_excel(sheet_url)
    st.success("Fusion rule data loaded from shared source.")

    # Clean column names
    data.columns = data.columns.str.strip().str.lower().str.replace(" ", "_")

    def extract_unique_values(column):
        if column not in data.columns:
            return []
        split_values = data[column].dropna().astype(str).str.split(',')
        flat_list = [item.strip() for sublist in split_values for item in sublist]
        return sorted(set(flat_list))

    countries = st.multiselect("Select Country Stakeholder(s):", options=extract_unique_values('country'))
    categories = st.multiselect("Select Category(s):", options=extract_unique_values('category'))
    project_types = st.multiselect("Select Project Type(s):", options=extract_unique_values('project_type'))

    # Match rules: all non-blank fields in rule must match user input
    def matches(row):
        def field_blocks(row_val, selected_vals):
            if pd.isna(row_val) or str(row_val).strip() == '':
                return False  # blank = wildcard
            if not selected_vals:
                return True  # rule is specific, but user didn't select
            rule_values = set(x.strip().lower() for x in str(row_val).split(',') if x.strip())
            selected_values = set(x.lower() for x in selected_vals)
            return not rule_values.intersection(selected_values)

        if field_blocks(row.get('country', ''), countries):
            return False
        if field_blocks(row.get('category', ''), categories):
            return False
        if field_blocks(row.get('project_type', ''), project_types):
            return False
        return True

    filtered = data[data.apply(matches, axis=1)]

    # Sort by team priority
    team_order = ['WIP', 'Content', 'Messaging', 'Management', 'Executive', 'Production']

    def extract_sort_key(team_val):
        for level in team_order:
            if level.lower() in str(team_val).lower():
                return team_order.index(level)
        return len(team_order)

    if not filtered.empty:
        filtered = filtered.sort_values(by='team', key=lambda col: col.map(extract_sort_key))

    st.markdown("---")
    st.subheader(f"Matching Assignments ({len(filtered)} found)")

    if not filtered.empty:
        st.dataframe(
            filtered[['name', 'team']].drop_duplicates().reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.warning("No matching assignments found.")

except Exception as e:
    st.error(f"Failed to load data: {e}")
