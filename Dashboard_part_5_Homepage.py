import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import sqlite3
from database_part3 import df_hourly_steps
from datawrangling_part4 import *

# === Page config ===
st.set_page_config(
    page_title="FitBit Analytics 2016",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

#=== Functions to connect to databases and load Data ===
@st.cache_data
def load_activity_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df_activity = pd.read_sql_query("SELECT * FROM daily_activity", conn)
    conn.close()
    return df_activity

@st.cache_data
def load_hourly_steps_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df_steps = pd.read_sql_query("SELECT * FROM hourly_steps", conn)
    conn.close()
    return df_steps

@st.cache_data
def load_heart_rate_data(database="fitbit_database.db"):
    conn = sqlite3.connect("fitbit_database.db")
    query = "SELECT * FROM heart_rate"
    df_heartrate = pd.read_sql_query(query, conn)
    conn.close()
    return df_heartrate

# Call functions
df_heart_rate = load_heart_rate_data()
df_steps = load_hourly_steps_data()
df_activity = load_activity_data()

# === Prepare df_overview ===
df_overview = df_activity.copy()
df_overview["ActivityDate"] = pd.to_datetime(df_overview["ActivityDate"], format="%m/%d/%Y")
df_overview["Id"] = df_overview["Id"].astype("Int64")
df_overview["Class"] = df_overview.groupby("Id")["Id"].transform("count").apply(
    lambda days: "Light" if days <= 10 else ("Moderate" if days <= 15 else "Heavy")
)

# === Main Title ===
st.title("FitBit Fitness Tracker Analytics 2016")
st.header("Summary Dashboard — 35 Fitbit Users")
st.markdown("Summary statistics and individual insights from a 2016 Fitbit study of 35 participants.")

st.divider()

# === Key Metrics ===
n_users = df_overview["Id"].nunique()
date_min = df_overview["ActivityDate"].min()
date_max = df_overview["ActivityDate"].max()
avg_steps = int(df_overview["TotalSteps"].mean())
avg_calories = int(df_overview["Calories"].mean())
avg_sedentary = int(df_overview["SedentaryMinutes"].mean())

st.markdown("#### Key Metrics")
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Users", n_users)
col2.metric("Study Start", date_min.strftime("%d/%m/%Y"))
col3.metric("Study End", date_max.strftime("%d/%m/%Y"))
col4.metric("Avg Daily Steps", f"{avg_steps:,}")
col5.metric("Avg Daily Calories", f"{avg_calories:,}")
col6.metric("Avg Sedentary Min", f"{avg_sedentary:,}")

st.divider()

# === Numerical Summary Table ===
st.markdown("#### Numerical Summary by User Class")

with st.expander("What do the user classes mean?"):
    st.markdown("""
    Users are classified based on how many days they recorded activity during the study period:
    
    - **Light user** — recorded 10 days or fewer
    - **Moderate user** — recorded between 11 and 15 days  
    - **Heavy user** — recorded 16 days or more
    """)

summary_table = (
    df_overview.groupby("Class")[["TotalSteps", "Calories", "VeryActiveMinutes", "SedentaryMinutes"]]
    .agg(["mean", "median", "std"])
    .round(1)
    .reindex(["Light", "Moderate", "Heavy"])
)
summary_table.columns = [" ".join(col) for col in summary_table.columns]
st.dataframe(summary_table, use_container_width=True)

st.divider()

# === Bar Chart ===
st.markdown("#### Average Daily Steps & Calories per User Class")
class_order = ["Light", "Moderate", "Heavy"]
class_avg = df_overview.groupby("Class")[["TotalSteps", "Calories"]].mean().reindex(class_order)

fig_bar, axes = plt.subplots(1, 2, figsize=(12, 5))
fig_bar.patch.set_facecolor("#0e1117")
colors = ["#4C72B0", "#DD8452", "#55A868"]

for ax in axes:
    ax.set_facecolor("#0e1117")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

axes[0].bar(class_avg.index, class_avg["TotalSteps"], color=colors)
axes[0].set_title("Average Daily Steps by User Class")
axes[0].set_xlabel("User Class")
axes[0].set_ylabel("Average Steps")
for i, v in enumerate(class_avg["TotalSteps"]):
    axes[0].text(i, v + 100, f"{int(v):,}", ha="center", fontsize=10, color="white")

axes[1].bar(class_avg.index, class_avg["Calories"], color=colors)
axes[1].set_title("Average Daily Calories by User Class")
axes[1].set_xlabel("User Class")
axes[1].set_ylabel("Average Calories")
for i, v in enumerate(class_avg["Calories"]):
    axes[1].text(i, v + 5, f"{int(v):,}", ha="center", fontsize=10, color="white")

plt.tight_layout()
st.pyplot(fig_bar)

st.divider()

# === Boxplot ===
st.markdown("#### Activity Distribution per Weekday by User Class")
activity_metric = st.selectbox("Choose Activity Metric", [
    "TotalSteps", "TotalDistance", "TrackerDistance", "VeryActiveDistance",
    "LoggedActivitiesDistance", "ModeratelyActiveDistance", "LightActiveDistance",
    "SedentaryActiveDistance", "VeryActiveMinutes", "FairlyActiveMinutes",
    "LightlyActiveMinutes", "SedentaryMinutes", "Calories"
])
fig, conclusion = plot_weekday_activity_per_class(df=df_activity.copy(), variable=activity_metric)
st.pyplot(fig)
st.markdown(conclusion)