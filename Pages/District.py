import streamlit as st
import pandas as pd

# Title
st.title("📍 District-level Insights")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Data/lsgd_data.csv")
    return df

df = load_data()

# Define custom LBType order
lbtype_order = ["Grama", "Municipality", "Corporation", "Block", "District"]
df["LBType"] = pd.Categorical(df["LBType"], categories=lbtype_order, ordered=True)

# Dropdown to select district
districts = sorted(df["District"].dropna().unique())
selected_district = st.selectbox("Select a District", districts)

# Filter to selected district and winners
df_district = df[(df["District"] == selected_district) & (df["Rank"] == 1)]

# Create pivot table
pivot_table = pd.pivot_table(
    df_district,
    index="Front",
    columns="LBType",
    values="Candidate",
    aggfunc="count",
    fill_value=0,
    margins=True,
    margins_name="Total"
)

# Reorder columns with Total at the end
ordered_columns = [col for col in lbtype_order if col in pivot_table.columns]
if "Total" in pivot_table.columns:
    ordered_columns.append("Total")
pivot_table = pivot_table[ordered_columns]

# Custom front order: UDF > LDF > NDA > OTH > others > Total
front_priority = ["UDF", "LDF", "NDA", "OTH"]
all_fronts = pivot_table.index.tolist()

# Extract other fronts not in the priority list or 'Total'
other_fronts = [f for f in all_fronts if f not in front_priority and f != "Total"]

# Final order
ordered_fronts = front_priority + sorted(other_fronts)
if "Total" in pivot_table.index:
    ordered_fronts.append("Total")

# Reorder the pivot table
pivot_table = pivot_table.loc[ordered_fronts]

# Style the table: make "Total" column bold
def highlight_total_col(val):
    return "font-weight: bold" if val.name == "Total" else ""

styled_table = pivot_table.style.applymap(
    lambda val: "font-weight: bold", subset=["Total"]
)

st.subheader(f"🏆 Seats Won by Front and LBType in {selected_district}")
st.dataframe(styled_table, use_container_width=True)

# --- UDF Performance in Panchayat / Municipality / Corporation Wards ---
st.subheader("🟦 UDF Performance in Panchayat / Municipality / Corporation Wards")

# Filter data: UDF candidates in Ward-tier, selected district
df_udf = df[
    (df["Front"] == "UDF") &
    (df["Tier"] == "Ward") &
    (df["District"] == selected_district)
]

# Total seats contested per party
contested = df_udf.groupby("Party").size().rename("Contested")

# Create pivot table with ranks as columns
rank_counts = pd.pivot_table(
    df_udf,
    index="Party",
    columns="Rank",
    values="Candidate",
    aggfunc="count",
    fill_value=0
)

# Rename Rank 1 to "Won"
if 1 in rank_counts.columns:
    rank_counts.rename(columns={1: "Won"}, inplace=True)

# Merge rank counts and contested
summary = pd.concat([rank_counts, contested], axis=1).fillna(0).astype(int)

# Add Hit Rate
summary["Hit Rate (%)"] = (summary["Won"] / summary["Contested"] * 100).round(2)

# Total row (renamed to "Contested")
summary.loc["Contested"] = summary.sum(numeric_only=True)
summary.loc["Contested", "Hit Rate (%)"] = round(
    (summary.loc["Contested", "Won"] / summary.loc["Contested", "Contested"]) * 100, 2
)

# Reorder columns: Won, other ranks, Contested, Hit Rate
cols = summary.columns.tolist()
cols_sorted = [col for col in cols if isinstance(col, int)]
if "Won" in summary.columns:
    cols_sorted = ["Won"] + sorted(cols_sorted)
cols_sorted += ["Contested", "Hit Rate (%)"]
summary = summary[cols_sorted]

# Apply formatting: integers for counts, 2 decimals for Hit Rate
format_dict = {col: "{:,.0f}" for col in summary.columns if col != "Hit Rate (%)"}
format_dict["Hit Rate (%)"] = "{:.2f}"

# Custom sort: IUML first, then INC, then rest alphabetically, then Contested last
party_order = ["IUML", "INC"]
other_parties = [p for p in summary.index if p not in party_order and p != "Contested"]
ordered_index = party_order + sorted(other_parties)

# Append 'Contested' row at the end
if "Contested" in summary.index:
    ordered_index.append("Contested")

summary = summary.loc[ordered_index]

# Display table
st.dataframe(summary.style.format(format_dict), use_container_width=True)

