import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("🧠 Other Party Insights")

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("Data/lsgd_data.csv")
    return df

df = load_data()

# Filter only Tier = Ward
#df = df[df["Tier"] == "Ward"].copy()

# --- Dropdowns for Party and District ---
parties = sorted(df["Party"].dropna().unique())
selected_party = st.selectbox(
    "Select a Party", parties, index=parties.index("IUML") if "IUML" in parties else 0
)

districts = ["Kerala"] + sorted(df["District"].dropna().unique())
selected_district = st.selectbox("Select a District", districts)

# --- Filter data based on selections ---
if selected_district == "Kerala":
    df_filtered = df[df["Party"] == selected_party].copy()
else:
    df_filtered = df[(df["Party"] == selected_party) & (df["District"] == selected_district)].copy()

df_party = df_filtered.copy()


# --- Table: Candidates <40 vs ≥40 and Win % ---
df_party["AgeGroup40"] = df_party["Age"].apply(lambda x: "Under 40" if x < 40 else "Over 40")

age_summary = (
    df_party.groupby("AgeGroup40")
    .agg(
        Contested=("Candidate", "count"),
        Won=("Rank", lambda x: (x == 1).sum())
    )
    .reset_index()
)

age_summary["Win %"] = (age_summary["Won"] / age_summary["Contested"] * 100).round(2)

# Reorder rows: Under 40 first
age_summary["SortOrder"] = age_summary["AgeGroup40"].map({"Under 40": 0, "Over 40": 1})
age_summary = age_summary.sort_values("SortOrder").drop(columns="SortOrder")

st.subheader(f"🧾 Candidate Age Split (Under vs Over 40) – {selected_party}")
st.dataframe(age_summary, use_container_width=True, hide_index=True)

# --- Pie Chart: Under 40 vs Over 40 ---
labels = age_summary["AgeGroup40"]
values = age_summary["Contested"]

fig_pie = go.Figure(data=[
    go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=["#AED6F1", "#F1948A"]),  # Blue for <40, Red for ≥40
        textinfo="label+percent",
    )
])

fig_pie.update_layout(
    title=f"🎂 Age Group Distribution – {selected_party}",
    height=350
)

st.plotly_chart(fig_pie, use_container_width=True)

# --- Age Category Function ---
def categorize_age(age):
    if age < 25:
        return "< 25"
    elif 25 <= age < 35:
        return "25 – 35"
    elif 35 <= age < 50:
        return "35 – 50"
    elif 50 <= age < 60:
        return "50 – 60"
    else:
        return "60+"

df_party["AgeCategory"] = df_party["Age"].apply(categorize_age)

# --- Bar Chart Data ---
age_chart_df = df_party.groupby("AgeCategory").agg(
    Contested=("Candidate", "count"),
    Won=("Rank", lambda x: (x == 1).sum())
).reset_index()

# Sort manually by category order
age_order = ["< 25", "25 – 35", "35 – 50", "50 – 60", "60+"]
age_chart_df["AgeCategory"] = pd.Categorical(age_chart_df["AgeCategory"], categories=age_order, ordered=True)
age_chart_df = age_chart_df.sort_values("AgeCategory")

# Melt to long format for bar chart
age_chart_long = age_chart_df.melt(
    id_vars="AgeCategory",
    value_vars=["Contested", "Won"],
    var_name="Status",
    value_name="Count"
)

# --- Bar Chart ---
st.subheader(f"📊 Age-Wise Performance – {selected_party}")

fig = px.bar(
    age_chart_long,
    x="AgeCategory",
    y="Count",
    color="Status",
    barmode="group",
    text="Count",
    labels={"AgeCategory": "Age Group"},
    color_discrete_map={
        "Contested": "#89CFF0",
        "Won": "#87BB62"
    }
)

fig.update_layout(
    xaxis_title="Age Group",
    yaxis_title="Number of Candidates",
    title="Contested vs Won by Age Category",
    legend_title="Status",
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# --- Table: Age Category vs Contested Count & % ---
age_dist = df_party.groupby("AgeCategory").agg(
    Contested=("Candidate", "count")
).reset_index()

age_dist["AgeCategory"] = pd.Categorical(age_dist["AgeCategory"], categories=age_order, ordered=True)
age_dist = age_dist.sort_values("AgeCategory")

total_contested_party = df_party.shape[0]

age_dist["% of Total Contested"] = (
    age_dist["Contested"] / total_contested_party * 100
).round(2)

st.subheader(f"📋 Age Distribution of Candidates – {selected_party}")
st.dataframe(age_dist, use_container_width=True, hide_index=True)

st.subheader(f"👥 Gender-wise Performance – {selected_party}")

# --- Gender Pie Chart ---
gender_counts = df_party["Gender"].value_counts().reset_index()
gender_counts.columns = ["Gender", "Count"]

fig_gender = go.Figure(data=[
    go.Pie(
        labels=gender_counts["Gender"],
        values=gender_counts["Count"],
        hole=0.3,
        marker=dict(colors=["#6FA8DC", "#F9CB9C"]),  # Blue for Male, Peach for Female
        textinfo="label+percent"
    )
])

fig_gender.update_layout(
    title="Gender Distribution of Candidates",
    height=350
)

st.plotly_chart(fig_gender, use_container_width=True)

# --- Gender Table ---
gender_table = (
    df_party.groupby("Gender")
    .agg(
        Contested=("Candidate", "count"),
        Won=("Rank", lambda x: (x == 1).sum())
    )
    .reset_index()
)

gender_table["Win %"] = (
    gender_table["Won"] / gender_table["Contested"] * 100
).round(2)

# Optional: Rename Gender values for clarity
gender_table["Gender"] = gender_table["Gender"].replace({"M": "Male", "F": "Female"})

st.dataframe(gender_table, use_container_width=True, hide_index=True)