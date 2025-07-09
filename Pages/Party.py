import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set page configuration

st.title("🏳️ Party-Level Analysis")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Data/lsgd_data.csv")
    return df

df = load_data()
df_ward = df[df["Tier"] == "Ward"].copy()

# Dropdown: Select Party (default = IUML)
parties = sorted(df_ward["Party"].dropna().unique())
selected_party = st.selectbox("Select a Party", parties, index=parties.index("IUML") if "IUML" in parties else 0)

# Dropdown: Select District (default = "Kerala" = all districts)
districts = ["Kerala"] + sorted(df_ward["District"].dropna().unique())
selected_district = st.selectbox("Select a District", districts)

# Filter according to district selection
if selected_district == "Kerala":
    df_filtered = df_ward.copy()
else:
    df_filtered = df_ward[df_ward["District"] == selected_district]

# Filter for selected party
df_party = df_filtered[df_filtered["Party"] == selected_party]

# Total votes across all parties (for percentage)
total_votes_all = df_filtered["Votes"].sum()
party_votes = df_party["Votes"].sum()
vote_percent = (party_votes / total_votes_all * 100) if total_votes_all > 0 else 0

# --- Vote Summary Table ---
summary_df = pd.DataFrame({
    "Party": [selected_party],
    "Total Votes": [int(party_votes)],
    "Vote Share (%)": [round(vote_percent, 2)]
})

st.subheader(f"🗳️ Total Votes for {selected_party} in {selected_district}")
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# --- Performance Metrics ---
st.subheader(f"📈 Performance Metrics – {selected_party} in {selected_district}")

seats_contested = df_party.shape[0]
seats_won = df_party[df_party["Rank"] == 1].shape[0]
strike_rate = (seats_won / seats_contested * 100) if seats_contested > 0 else 0

perf_df = pd.DataFrame({
    "Party": [selected_party],
    "Seats Contested": [seats_contested],
    "Seats Won": [seats_won],
    "Strike Rate (%)": [round(strike_rate, 2)]
})

st.dataframe(perf_df, use_container_width=True, hide_index=True)
# --- Doughnut Chart ---
fig = go.Figure(data=[
    go.Pie(
        labels=["Won", "Not Won"],
        values=[seats_won, seats_contested - seats_won],
        hole=0.5,
        marker_colors=["#87BB62", "#F89B78"]
    )
])
fig.update_layout(title="🎯 Strike Rate", showlegend=True, height=300, margin=dict(t=40, b=0))
st.plotly_chart(fig, use_container_width=True)


# --- Pivot Table: LBType × Rank ---
st.subheader(f"📊 Count of Positions – {selected_party} in {selected_district}")

pivot = pd.pivot_table(
    df_party,
    index="LBType",
    columns="Rank",
    values="Candidate",
    aggfunc="count",
    fill_value=0,
    margins=True,
    margins_name="Contested"
)

if 1 in pivot.columns:
    pivot.rename(columns={1: "Won"}, inplace=True)

rank_cols = [col for col in pivot.columns if isinstance(col, int)]
column_order = ["Won"] if "Won" in pivot.columns else []
column_order += sorted(rank_cols)
if "Contested" in pivot.columns:
    column_order += ["Contested"]

pivot = pivot[column_order]

# Add Strike Rate
if "Won" in pivot.columns and "Contested" in pivot.columns:
    pivot["Strike Rate (%)"] = (pivot["Won"] / pivot["Contested"] * 100).round(2)
else:
    pivot["Strike Rate (%)"] = 0.0

pivot = pivot.reset_index()
st.dataframe(pivot, use_container_width=True, hide_index=True)

# --- IUML and Related Parties Comparison Table ---
if selected_party == "IUML":
    st.subheader(f"📋 IUML and Allied Party Comparison – {selected_district}")

    # Parties to compare
    compare_parties = ["IUML", "SDPI", "WPI", "NSC", "INL", "PDP"]

    # Filter: Tier = Ward + selected district
    df_tier_ward = df[df["Tier"] == "Ward"].copy()
    if selected_district != "Kerala":
        df_tier_ward = df_tier_ward[df_tier_ward["District"] == selected_district]

    # Total votes of all parties in the filtered set (for vote share)
    total_votes_all = df_tier_ward["Votes"].sum()

    # Filter only selected comparison parties
    df_cmp = df_tier_ward[df_tier_ward["Party"].isin(compare_parties)]

    summary_rows = []

    for party in compare_parties:
        party_df = df_cmp[df_cmp["Party"] == party]
        contested = len(party_df)
        won = len(party_df[party_df["Rank"] == 1])
        votes = party_df["Votes"].sum()
        strike_rate = (won / contested * 100) if contested > 0 else 0
        vote_share = (votes / total_votes_all * 100) if total_votes_all > 0 else 0

        summary_rows.append({
            "Party": party,
            "Won": won,
            "Contested": contested,
            "Strike Rate (%)": round(strike_rate, 2),
            "Votes Secured": int(votes),
            "Vote Share (%)": round(vote_share, 2)
        })

    compare_df = pd.DataFrame(summary_rows)
    compare_df = compare_df.sort_values("Votes Secured", ascending=False).reset_index(drop=True)

    st.dataframe(compare_df, use_container_width=True, hide_index=True)

# --- District-wise IUML + Allies Summary ---
if selected_party == "IUML" and selected_district == "Kerala":
    st.subheader("🌍 District-wise Performance – IUML & Allied Parties (Kerala)")

    allies = ["IUML", "SDPI", "INL", "WPI", "NSC", "PDP"]
    df_allies = df_ward[df_ward["Party"].isin(allies)]

    # --- Table 1: Seats Won ---
    won_pivot = pd.pivot_table(
        df_allies[df_allies["Rank"] == 1],
        index="District",
        columns="Party",
        values="Candidate",
        aggfunc="count",
        fill_value=0
    ).reset_index()

    won_cols = ["District"] + [p for p in allies if p in won_pivot.columns]
    won_pivot = won_pivot[won_cols]

    def highlight_if_iuml_lower(row):
        iuml = row.get("IUML", 0)
        for party in allies:
            if party != "IUML" and row.get(party, 0) > iuml:
                return ["background-color: #FADBD8"] * len(row)
        return [""] * len(row)

    st.markdown("#### 🏆 Seats Won by District")
    st.dataframe(
        won_pivot.style.apply(highlight_if_iuml_lower, axis=1),
        use_container_width=True
    )

    # --- Table 2: Votes Secured ---
    vote_pivot = pd.pivot_table(
        df_allies,
        index="District",
        columns="Party",
        values="Votes",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    vote_cols = ["District"] + [p for p in allies if p in vote_pivot.columns]
    vote_pivot = vote_pivot[vote_cols]

    st.markdown("#### 🗳️ Votes Secured by District")
    st.dataframe(
        vote_pivot.style.apply(highlight_if_iuml_lower, axis=1),
        use_container_width=True
    )
