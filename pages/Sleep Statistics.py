import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import sqlite3

from datawrangling_part4 import *

# === Functions to connect to databases and load Data ===
@st.cache_data
def load_sleep_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    # Set up query
    query = """
    SELECT *
    FROM minute_sleep
    """
    df_sleep = pd.read_sql_query(query, conn)
    # Convert Date to datetime and ID to category
    df_sleep["date"] = pd.to_datetime(df_sleep["date"])
    df_sleep["Id"] = df_sleep["Id"].astype("int64")
    conn.close()
    return df_sleep

df_sleep = load_sleep_data()


# === Sidebar ===
st.sidebar.markdown(
    """
    <div style="padding: 12px 4px 8px 4px;">
        <div style="color:white; font-size:1.1rem; font-weight:700; margin-bottom:4px;">Sleep Statistics</div>
        <div style="color:#9B9EAC; font-size:0.78rem; line-height:1.5;">
            Per-user sleep stages and duration. Select a date to explore nightly patterns.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()
st.sidebar.markdown("**Select a User**")
available_ids = sorted(df_sleep["Id"].dropna().unique().tolist())
user_id = st.sidebar.selectbox("Select a User ID", available_ids)
#quick stats for selected user,
user_data = df_sleep[df_sleep["Id"] == user_id]
df_user_sleep = (user_data.groupby(["logId"]).
            agg(
    start_date=("date", "min"),#Date sleep period started
    end_date=("date", "max"), #Date sleep period ended
    Duration =("logId", "count") #Duration: sleep duration in mins
).reset_index())
df_user_sleep["Duration"] = df_user_sleep["Duration"].apply(lambda x: x/60)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Stats for User {user_id}**")
st.sidebar.metric("Days Recorded", len(df_user_sleep))
st.sidebar.metric("Avg Hours Slept", f"{int(df_user_sleep['Duration'].mean()):,}")

# Date filter: only allow dates that exist for this user
st.sidebar.markdown("---")
st.sidebar.markdown("**Date Filter for Sleep Data**")

user_dates = sorted(df_user_sleep["end_date"].dt.date.unique())

#date selector
start_date = st.sidebar.selectbox(
    "Select start date",
    options=user_dates,
    index=0,
    format_func=lambda d: d.strftime("%d/%m/%Y")
)

st.sidebar.write(f"Selected: {start_date.strftime('%d/%m/%Y')}")

# Page header
st.title("Sleep Statistics")
st.caption(f"User {user_id} · {start_date.strftime('%d/%m/%Y')}")
st.divider()

#generate figures
fig_sleep = plot_sleep(user_id, start_date, df_sleep)

fig_sleep_summary = plot_sleep_summary(user_id=user_id, start_date=start_date, df= df_sleep)

fig_sleep_overview = plot_sleep_overview(user_id, df_sleep)
#plot figures with warnings for empty function calls
if fig_sleep is not None:
    st.pyplot(fig_sleep)
else:
    st.warning("No sleep data available for this date.")

if fig_sleep_summary is not None:
    st.pyplot(fig_sleep_summary)
else:
    st.warning("No sleep data available for this date.")

if fig_sleep_overview is not None:
    st.pyplot(fig_sleep_overview)
else:
    st.warning("No sleep overview available for this date.")