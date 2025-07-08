import streamlit as st
import pandas as pd
import math
import altair as alt


st.title("🏘️ Local Body-Level Insights")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Data/lsgd_data.csv")
    return df

df = load_data()

# Ensure Tier is treated correctly
df = df[df["Tier"] == "Ward"]

# Dropdown: Select District
districts = sorted(df["District"].dropna().unique())
selected_district = st.selectbox("Select a District", districts)

# Dropdown: Select LBName based on selected District
lbnames = sorted(df[df["District"] == selected_district]["LBName"].dropna().unique())
selected_lb = st.selectbox("Select a Local Body", lbnames)

# Filter data to selected Local Body & only winners
df_filtered = df[
    (df["District"] == selected_district) &
    (df["LBName"] == selected_lb) &
    (df["Rank"] == 1)
]

# Count seats won by each Front
front_summary = (
    df_filtered.groupby("Front")
    .size()
    .reset_index(name="Seats Won")
    .sort_values(by="Seats Won", ascending=False)
)

# Custom order: UDF > LDF > NDA > OTH > others
front_priority = ["UDF", "LDF", "NDA", "OTH"]
others = [f for f in front_summary["Front"] if f not in front_priority]
ordered_fronts = front_priority + sorted(others)
front_summary["Front"] = pd.Categorical(front_summary["Front"], categories=ordered_fronts, ordered=True)
front_summary = front_summary.sort_values("Front")

# Reset index to remove row index in Streamlit table
front_summary = front_summary.reset_index(drop=True)

# Display table without index
st.subheader(f"🏆 Seats Won by Front in {selected_lb}, {selected_district}")
st.dataframe(front_summary, use_container_width=True, hide_index=True)


# --- Visualize Seats Won by Front ---
st.subheader(f"📊 Stacked Bar Chart – Party-wise Wins by Front in {selected_lb}")

# Filter winners from the selected Local Body
df_winners = df[
    (df["District"] == selected_district) &
    (df["LBName"] == selected_lb) &
    (df["Rank"] == 1)
].copy()

# --- Dynamic Color Mapping ---

# 1. Define explicit color mapping for key parties
party_specific_colors = {
    'IUML': '#2E8B57',      # Sea Green for IUML
    'INC': '#1F77B4',       # Standard Blue for INC
    'CPM': '#D62728',       # Standard Red for CPM
    'BJP': '#FF7F0E',       # Standard Orange for BJP
    'IND': '#7F7F7F'        # Grey for Independent (OTH)
}

# 2. Define color palettes for each Front
front_palettes = {
    'UDF': ['#85C1E9', '#5DADE2', '#A9D0F5', '#0B5394'], # Blue shades
    'LDF': ['#F08080', '#FF9896', '#A52A2A', '#8B0000'], # Red shades
    'NDA': ['#FFBB78', '#F7B731', '#FFA500', '#CC7722'], # Orange/Saffron shades
    'OTH': ['#A0A0A0', '#5F5F5F', '#BFBFBF']            # Grey shades
}

# 3. Build the final color map for all parties
final_party_color_map = {}
for _, row in df_winners.iterrows():
    party = row['Party']
    front = row['Front']

    if party in party_specific_colors:
        final_party_color_map[party] = party_specific_colors[party]
    elif party not in final_party_color_map:
        if front in front_palettes:
            palette = front_palettes[front]
            assigned_count = len([p for p in final_party_color_map if p not in party_specific_colors and df_winners[df_winners['Party'] == p]['Front'].iloc[0] == front])
            final_party_color_map[party] = palette[assigned_count % len(palette)]
        else:
            final_party_color_map[party] = '#CCCCCC' # Default grey

# --- Data Aggregation for the Chart ---
# Group by Front and Party to get the count of seats won
df_agg = df_winners.groupby(['Front', 'Party']).size().reset_index(name='Seats Won')


# --- Create the Altair Chart ---

# Base chart layer for the bars
base_chart = alt.Chart(df_agg).mark_bar().encode(
    # Format axis to show whole numbers using format='d' (for integer)
    x=alt.X('sum(Seats Won):Q',
            title='Number of Seats Won',
            stack='zero',
            axis=alt.Axis(format='d')), # <-- MODIFICATION: Format axis labels as integers

    # Update the Y-axis title
    y=alt.Y('Front:N',
            sort='-x',
            title='Front/Party'), # <-- MODIFICATION: Changed axis title

    # Color encoding by Party using the custom map
    color=alt.Color('Party:N',
                    scale=alt.Scale(domain=list(final_party_color_map.keys()),
                                    range=list(final_party_color_map.values())),
                    legend=alt.Legend(
                        title="Party",
                        orient='bottom',
                        columns=3,
                        labelLimit=200
                    )),

    # Tooltip to show details on hover
    tooltip=[
        alt.Tooltip('Front:N', title='Front'),
        alt.Tooltip('Party:N', title='Party'),
        alt.Tooltip('sum(Seats Won):Q', title='Seats Won')
    ]
)

# Text layer for labeling the bars
text_labels = base_chart.mark_text(
    align='center',
    baseline='middle',
    color='white',
    dx= -8 # Nudge labels slightly left for better centering
).encode(
    text=alt.Text('sum(Seats Won):Q', format='.0f') # Display the count of seats
)

# Combine the bar chart and the text labels
final_chart = (base_chart + text_labels).properties(
    title=f'Party-wise Seat Distribution by Front in {selected_lb}'
)

# Display the chart in Streamlit
st.altair_chart(final_chart, use_container_width=True)

# --- UDF Performance in the Selected Local Body ---
st.subheader(f"🔷 UDF Performance in {selected_lb}, {selected_district}")

# Filter UDF candidates in selected Local Body
df_udf = df[
    (df["Front"] == "UDF") &
    (df["District"] == selected_district) &
    (df["LBName"] == selected_lb)
]

# Create pivot: Party (rows) × Rank (columns)
udf_pivot = pd.pivot_table(
    df_udf,
    index="Party",
    columns="Rank",
    values="Candidate",
    aggfunc="count",
    fill_value=0
)

# Optional: add Total row
udf_pivot.loc["Total"] = udf_pivot.sum(numeric_only=True)

# Sort rank columns numerically
numeric_cols = sorted([col for col in udf_pivot.columns if isinstance(col, int)])
udf_pivot = udf_pivot[numeric_cols]

# Reset index for clean display
udf_pivot = udf_pivot.reset_index()

# Display the table
st.dataframe(udf_pivot, use_container_width=True, hide_index=True)



# --- IUML Performance by Strength ---
st.subheader(f"🟢 IUML Performance by Strength in {selected_lb}, {selected_district}")

# Filter for IUML in selected LB
df_iuml = df[
    (df["District"] == selected_district) &
    (df["LBName"] == selected_lb) &
    (df["Party"] == "IUML")
]

# Group by Strength
iuml_summary = (
    df_iuml.groupby("Strength")
    .agg(
        Wards_Count=("WardName", "count"),
        Ward_Names=("WardName", lambda x: ", ".join(sorted(x.unique())))
    )
    .reset_index()
    .sort_values("Strength", key=lambda s: pd.Categorical(s, categories=[
        "500+", "200 - 499", "100 - 199", "50 - 99", "1 - 49", "0",
        "-1 to -49", "-50 to -99", "-100 to -199", "-200 to -499", "-500+"
    ], ordered=True))
)

# Display the table
st.dataframe(iuml_summary, use_container_width=True, hide_index=True)

st.subheader(f"📋 Ward-wise Results – {selected_lb}, {selected_district}")

# Filter to selected district + LB
df_lb = df[
    (df["District"] == selected_district) &
    (df["LBName"] == selected_lb)
]

# Get winners (Rank 1)
winners = df_lb[df_lb["Rank"] == 1].copy()
# Get runners-up (Rank 2)
trailers = df_lb[df_lb["Rank"] == 2].copy()

# Merge winners and trailers on WardCode
merged = pd.merge(
    winners,
    trailers,
    on="WardCode",
    suffixes=("_win", "_trail")
)

# Construct final table
final_table = pd.DataFrame({
    "Sl. Code": merged["WardCode"].astype(str).str[-2:],  # Last 2 digits of LBCode
    "Ward Name": merged["WardName_win"],
    "Won": merged["Candidate_win"],
    "Won Party": merged["Party_win"],
    "Lead": merged["Lead_win"],
    "Trail": merged["Party_trail"] + " (" + merged["Candidate_trail"] + ")"
})

# Convert Sl. Code to int for sorting (removing non-numeric artifacts)
final_table["Sl. Code"] = final_table["Sl. Code"].astype(int)
final_table = final_table.sort_values("Sl. Code").reset_index(drop=True)

# Display the table
st.dataframe(final_table, use_container_width=True, hide_index=True)


