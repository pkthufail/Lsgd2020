import streamlit as st
import pandas as pd
import math

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

import altair as alt
st.subheader(f"📊 Stacked Bar Chart – Party-wise Wins by Front in {selected_lb}")

# Filter winners from selected Local Body
df_winners = df[
    (df["District"] == selected_district) &
    (df["LBName"] == selected_lb) &
    (df["Rank"] == 1)
].copy()


# 1. Define explicit color mapping for specific parties (highest priority)
# Add any party here that should *always* have a specific color, regardless of Front logic.
# This ensures consistency for key parties.
party_specific_colors = {
    'IUML': '#2E8B57',      # Specific Green for IUML
    'INC': '#1F77B4',       # Deep Blue for INC
    'CPM': '#D62728',       # Strong Red for CPM
    'BJP': '#FF7F0E',       # Dark Orange (Saffron) for BJP
    'IND': '#7F7F7F'        # Grey for Independent (OTH)
    # Add more specific party colors here as needed
}

# 2. Define general color palettes for each Front (for parties not explicitly mapped)
# These will be used to generate consistent shades for new or less prominent parties within a Front.
front_palettes = {
    'UDF': ['#85C1E9', '#5DADE2', '#A9D0F5', '#0B5394'], # Lighter to darker blues
    'LDF': ['#F08080', '#FF9896', '#A52A2A', '#8B0000'], # Lighter to darker reds
    'NDA': ['#FFBB78', '#F7B731', '#FFA500', '#CC7722'], # Lighter to darker oranges/saffrons
    'OTH': ['#A0A0A0', '#5F5F5F', '#BFBFBF']             # Lighter to darker greys
}

# 3. Build the final party-to-color map
# This map will hold a unique color for every party that appears in the data.
final_party_color_map = {}

# Process existing parties in df_winners
for index, row in df_winners.iterrows():
    party = row['Party']
    front = row['Front']

    if party in party_specific_colors:
        final_party_color_map[party] = party_specific_colors[party]
    elif party not in final_party_color_map: # Assign a new color if not already assigned
        # Find the next available color from the front's palette
        if front in front_palettes:
            assigned_count = len([p for p, c in final_party_color_map.items() if p not in party_specific_colors and df_winners[df_winners['Party'] == p]['Front'].iloc[0] == front])
            palette = front_palettes[front]
            final_party_color_map[party] = palette[assigned_count % len(palette)]
        else:
            final_party_color_map[party] = '#CCCCCC' # Default if Front is unknown


# 4. Assign colors to the DataFrame using the final_party_color_map
df_winners['custom_color'] = df_winners['Party'].map(final_party_color_map)

# Handle any parties that might not have been mapped (e.g., if a new party appears after map generation)
df_winners['custom_color'].fillna('#CCCCCC', inplace=True)


# Create the Altair chart
# Using 'Front' on Y-axis for horizontal bars and sorting by Rank
chart = alt.Chart(df_winners).mark_bar().encode(
    y=alt.Y('Front:N', sort='-x', title='Front'), # Sort by Rank descending
    x=alt.X('Rank:Q', title='Rank'),
    
    # Use the 'Party' column for coloring, but apply our custom color scale
    # This correctly generates a legend based on 'Party'
    color=alt.Color('Party:N', scale=alt.Scale(domain=list(final_party_color_map.keys()), 
                                              range=list(final_party_color_map.values())),
                    legend=alt.Legend(title="Party", columns=2, labelLimit=200)), # Adjust columns for better layout
    
    # Add tooltips for detailed info on hover
    tooltip=['Front', 'Party', 'Rank']
).properties(
    title='Election Ranks by Front and Party'
)

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)


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


