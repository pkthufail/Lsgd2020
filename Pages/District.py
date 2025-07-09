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
selected_district = st.selectbox("Select a District", districts, index=districts.index("MALAPPURAM"))

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

# Reset index so "Front" becomes a column
pivot_table_reset = pivot_table.reset_index()

# Function to color based on Front
def front_row_style(row):
    color_map = {
        "UDF": "#D6EAF8",     # Light Blue
        "LDF": "#F5B7B1",     # Light Red
        "NDA": "#FAD7A0",     # Saffron
        "OTH": "#D5DBDB",     # Grey
    }
    color = color_map.get(row["Front"], "")
    return [f"background-color: {color}"] * len(row) if color else [""] * len(row)

styled_table = pivot_table_reset.style \
    .apply(front_row_style, axis=1) \
    .applymap(lambda v: "font-weight: bold", subset=["Total"])

# Display
st.subheader(f"🏆 Seats Won by Front and LBType in {selected_district}")
st.dataframe(styled_table, use_container_width=True, hide_index=True)

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

# Add total row (index = 'Total', but column name remains 'Contested')
summary.loc["Total"] = summary.sum(numeric_only=True)
summary.loc["Total", "Hit Rate (%)"] = round(
    (summary.loc["Total", "Won"] / summary.loc["Total", "Contested"]) * 100, 2
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

# Reset index so "Party" becomes a column
summary_reset = summary.reset_index()

# Color styling function
def party_row_style(row):
    color_map = {
        "IUML": "#ABEBC6",    # Light Green
        "INC": "#AED6F1",     # Light Blue
    }
    color = color_map.get(row["Party"], "")
    return [f"background-color: {color}"] * len(row) if color else [""] * len(row)

styled_summary = summary_reset.style \
    .apply(party_row_style, axis=1) \
    .format(format_dict)

st.dataframe(styled_summary, use_container_width=True, hide_index=True)

# --- IUML Performance by Strength Category ---
st.subheader("📶 IUML Performance by Strength")

# Filter IUML at Ward level
df_iuml = df[
    (df["District"] == selected_district) &
    (df["Party"] == "IUML") &
    (df["Tier"] == "Ward")
]

# Count wards per strength
strength_summary = (
    df_iuml.groupby("Strength")
    .agg(Wards=("WardName", "count"))
    .reset_index()
)

# Define logical order of strength categories
strength_order = [
    "-500 or less", "-200 to -499", "-100 to -199", "-50 to -99", "-1 to -49",
    "0",
    "1-49", "50-99", "100-199", "200-499", "500+"
]

# Apply ordering
strength_summary["Strength"] = pd.Categorical(strength_summary["Strength"], categories=strength_order, ordered=True)
strength_summary = strength_summary.sort_values("Strength")

# Display table
st.dataframe(strength_summary, use_container_width=True, hide_index=True)

# --- Visualization: Bar Chart ---
import plotly.express as px

# Prepare mirrored bar chart
mirror_df = strength_summary.copy()
mirror_df["Display_Wards"] = mirror_df.apply(
    lambda row: -row["Wards"] if str(row["Strength"]).startswith("-") else row["Wards"],
    axis=1
)

# Assign colors
mirror_df["Color"] = mirror_df["Strength"].apply(
    lambda x: "#E74C3C" if str(x).startswith("-") else "#5DADE2"  # Red vs Blue
)

# Create bar chart
fig_strength = px.bar(
    mirror_df,
    x="Strength",
    y="Display_Wards",
    text="Wards",
    color="Color",
    color_discrete_map="identity",  # Use custom color per bar
    title="📶 IUML Ward Distribution by Strength Category (Mirrored View)"
)

# Update layout for symmetrical display
fig_strength.update_layout(
    xaxis_title="Strength Category",
    yaxis_title="Number of Wards",
    height=500,
    showlegend=False,
    yaxis=dict(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='black'
    )
)

# Display chart
st.plotly_chart(fig_strength, use_container_width=True)

# --- Summary Table: Seats Won by Front per LB (Ward Tier only) ---
st.subheader(f"🏘️ Seats Won by Front in Each LB – {selected_district}")

# Filter for Ward tier winners in selected district
df_lb_fronts = df[
    (df["District"] == selected_district) &
    (df["Tier"] == "Ward") &
    (df["Rank"] == 1)
]

# Group by LBCode and Front to count seats
lb_summary = (
    df_lb_fronts.groupby(["LBCode", "LBName", "Front"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# Ensure all major fronts exist as columns
for front in ["UDF", "LDF", "NDA", "OTH"]:
    if front not in lb_summary.columns:
        lb_summary[front] = 0

# Add Sl No from LBCode (first letter + last 2 digits)
lb_summary["Sl No"] = lb_summary["LBCode"].astype(str).str[0] + lb_summary["LBCode"].astype(str).str[-2:]

# Reorder columns
columns_order = ["Sl No", "LBName", "UDF", "LDF", "NDA", "OTH"]
lb_summary = lb_summary[columns_order].sort_values("LBName").reset_index(drop=True)

# Display the table
st.dataframe(lb_summary, use_container_width=True, hide_index=True)