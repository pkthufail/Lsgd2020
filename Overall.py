import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Overall",
    layout="wide"
)
st.title("🗺️ Kerala Local Body Election 2020 - Dashboard")

# st.markdown("""
# Welcome to the **Kerala Local Body Election Dashboard**. This app offers detailed insights into the 2020 local body elections across Kerala. Navigate through the pages to explore:

# - **District**: View front-wise and party-wise performance in each district.
# - **Local Body**: Analyze party strength and ward-level results within a selected local body.
# - **Party**: Dive into the overall performance of a selected party across the state or district.
# - **Other**: Explore candidate-level trends by age, gender, and performance of selected parties.
# """)

st.subheader("📊 Overall Summary")

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("Data/lsgd_data.csv")
    return df

df = load_data()
df = df[df["Rank"] == 1].copy()  # Only winners

# --- Tabs ---
tab1, tab2 = st.tabs(["🏆 Seats Won", "📉 Vote Share"])

with tab1: 
    st.subheader("🏅 Number of Seats Won by Front")

    lbtype_order = ["Grama", "Municipality", "Corporation", "Block", "District"]
    df["LBType"] = pd.Categorical(df["LBType"], categories=lbtype_order, ordered=True)

    # Table: Front × LBType
    front_pivot = pd.pivot_table(
        df,
        index="Front",
        columns="LBType",
        values="Candidate",
        aggfunc="count",
        fill_value=0,
        margins=True,
        margins_name="Total"
    ).reset_index()

    # --- Reorder rows
    front_order = ["UDF", "LDF", "NDA", "OTH", "Total"]
    front_pivot["Front"] = pd.Categorical(front_pivot["Front"], categories=front_order, ordered=True)
    front_pivot = front_pivot.sort_values("Front")

    # --- Color style function
    def style_front_row(row):
        color_map = {
            "UDF": "#D6EAF8",     # Light Blue
            "LDF": "#F5B7B1",     # Light Red
            "NDA": "#FAD7A0",     # Saffron
            "OTH": "#D5DBDB",     # Grey
            "Total": "#EAECEE"    # Light Gray for total
        }
        color = color_map.get(row["Front"], "")
        return [f"background-color: {color}"] * len(row) if color else [""] * len(row)

    # Apply styling
    styled_front_table = front_pivot.style.apply(style_front_row, axis=1)

    st.dataframe(styled_front_table, use_container_width=True, hide_index=True)

    # Expanders: Party-wise Seats per Front
    front_list = ["UDF", "LDF", "NDA", "OTH"]
    for front in front_list:
        with st.expander(f"{front} – Party-wise Breakdown"):
            df_front = df[df["Front"] == front]

        # Create pivot without margins row
            party_pivot = pd.pivot_table(
                df_front,
                index="Party",
                columns="LBType",
                values="Candidate",
                aggfunc="count",
                fill_value=0
            )

            # Add Total column manually
            party_pivot["Total"] = party_pivot.sum(axis=1)

            # Sort by Total descending
            party_pivot = party_pivot.sort_values("Total", ascending=False).reset_index()

            st.dataframe(party_pivot, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🗳️ Total Vote Share by Front")

    # Load full data (not just winners)
    df_votes = load_data()
    df_votes = df_votes[df_votes["Tier"] == "Ward"].copy()  # Exclude block and district tiers
    df_votes = df_votes[df_votes["Votes"].notna()]  # Remove rows with missing votes

    # Total votes
    total_votes = df_votes["Votes"].sum()

    # --- Table: Front-wise Vote Share ---
    front_votes = (
        df_votes.groupby("Front")
        .agg(Votes=("Votes", "sum"))
        .reset_index()
        .sort_values("Votes", ascending=False)
    )
    front_votes["% Share"] = (front_votes["Votes"] / total_votes * 100).round(2)

    st.dataframe(front_votes, use_container_width=True, hide_index=True)

    # --- Expanders: Party-wise Vote Share by Front ---
    for front in ["UDF", "LDF", "NDA", "OTH"]:
        
        with st.expander(f"{front} – Party-wise Vote Share"):
            df_front = df_votes[df_votes["Front"] == front]
            front_total = df_front["Votes"].sum()

            party_votes = (
                df_front.groupby("Party")
                .agg(Votes=("Votes", "sum"))
                .reset_index()
                .sort_values("Votes", ascending=False)
            )
            party_votes[r"% Front Share"] = (
                party_votes["Votes"] / front_total * 100
            ).round(2)
            
            party_votes[r"% Total Share"] = (
                party_votes["Votes"] / total_votes * 100
            ).round(2)

            st.dataframe(party_votes, use_container_width=True, hide_index=True)