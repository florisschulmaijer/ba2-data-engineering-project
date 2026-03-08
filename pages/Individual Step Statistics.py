import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import sqlite3

from datawrangling_part4 import *

# === Functions to connect to databases and load Data ===
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

# Call functions
df_steps = load_hourly_steps_data()
df_activity = load_activity_data()

# Prepare df_overview
df_overview = df_activity.copy()
df_overview["ActivityDate"] = pd.to_datetime(df_overview["ActivityDate"], format="%m/%d/%Y")
df_overview["Id"] = df_overview["Id"].astype("Int64")
df_overview["Class"] = df_overview.groupby("Id")["Id"].transform("count").apply(
    lambda days: "Light" if days <= 10 else ("Moderate" if days <= 15 else "Heavy")
)

st.title("Individual User Step Statistics")

# === Sidebar ===
st.sidebar.title("Individual Users")
st.sidebar.markdown("Select a user ID to view individual step insights.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Select a User**")
available_ids = sorted(df_overview["Id"].dropna().unique().tolist())
user_id = st.sidebar.selectbox("Select a User ID", available_ids)

# Quick stats for selected user
user_data = df_overview[df_overview["Id"] == user_id]
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Stats for User {user_id}**")
st.sidebar.metric("User Class", user_data["Class"].iloc[0])
st.sidebar.metric("Days Recorded", len(user_data))
st.sidebar.metric("Avg Steps", f"{int(user_data['TotalSteps'].mean()):,}")
st.sidebar.metric("Avg Calories", f"{int(user_data['Calories'].mean()):,}")

# Progress bar comparison
st.sidebar.markdown("---")
st.sidebar.markdown("**How does this user compare?**")
avg_steps_all = int(df_overview["TotalSteps"].mean())
user_avg_steps = int(user_data["TotalSteps"].mean())
steps_percentile = (df_overview.groupby("Id")["TotalSteps"].mean() < user_avg_steps).mean()

if steps_percentile >= 0.5:
    st.sidebar.success(f"Above average — top {int((1 - steps_percentile) * 100)}% of users in daily steps")
else:
    st.sidebar.info(f"Below average — bottom {int(steps_percentile * 100)}% of users in daily steps")

st.sidebar.markdown(f"Their avg: **{user_avg_steps:,}** steps vs group avg: **{avg_steps_all:,}** steps")
st.sidebar.progress(min(user_avg_steps / (avg_steps_all * 2), 1.0))

# Date filter: only allow dates that exist for this user
st.sidebar.markdown("---")
st.sidebar.markdown("**Date Filter**")
user_dates = sorted(user_data["ActivityDate"].dt.date.unique())

start_date = st.sidebar.selectbox(
    "Select start date",
    options=user_dates,
    index=0,
    format_func=lambda d: d.strftime("%d/%m/%Y")
)
end_date = st.sidebar.selectbox(
    "Select end date",
    options=user_dates,
    index=len(user_dates) - 1,
    format_func=lambda d: d.strftime("%d/%m/%Y")
)

st.sidebar.write(f"Selected: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")

if start_date > end_date:
    st.sidebar.warning("Start date must be before end date.")
else:
    fig_steps = plot_daily_steps(user_id=user_id, start_date=start_date, end_date=end_date, df=df_steps)
    st.pyplot(fig_steps)
