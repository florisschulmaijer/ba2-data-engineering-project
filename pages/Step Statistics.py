import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3
from datawrangling_part4 import plot_daily_steps

# === Page config ===
st.set_page_config(
    page_title="Step Statistics",
    page_icon="fitbit",
    layout="wide",
    initial_sidebar_state="expanded"
)

BG_COLOR = "#111420"
C_BLUE   = "#4C9BE8"
C_ORANGE = "#E8834C"
C_GREEN  = "#52C97A"

def style_ax(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

# === Data loading ===
@st.cache_data
def load_activity_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM daily_activity", conn)
    conn.close()
    return df

@st.cache_data
def load_hourly_steps_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM hourly_steps", conn)
    conn.close()
    return df

df_steps = load_hourly_steps_data()
df_activity = load_activity_data()

# Prepare overview
df_overview = df_activity.copy()
df_overview["ActivityDate"] = pd.to_datetime(df_overview["ActivityDate"], format="%m/%d/%Y")
df_overview["Id"] = df_overview["Id"].astype("Int64")
df_overview["Class"] = df_overview.groupby("Id")["Id"].transform("count").apply(
    lambda days: "Light" if days <= 10 else ("Moderate" if days <= 15 else "Heavy")
)

# Sidebar
st.sidebar.markdown(
    """
    <div style="padding: 12px 4px 8px 4px;">
        <div style="color:white; font-size:1.1rem; font-weight:700; margin-bottom:4px;">Step Statistics</div>
        <div style="color:#9B9EAC; font-size:0.78rem; line-height:1.5;">
            Per-user hourly step patterns across a selected date range.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()

available_ids = sorted(df_overview["Id"].dropna().unique().tolist())
user_id = st.sidebar.selectbox("User ID", available_ids)
user_data = df_overview[df_overview["Id"] == user_id]

st.sidebar.divider()
user_dates = sorted(user_data["ActivityDate"].dt.date.unique())
start_date = st.sidebar.selectbox(
    "Start date", options=user_dates, index=0,
    format_func=lambda d: d.strftime("%d/%m/%Y")
)
end_date = st.sidebar.selectbox(
    "End date", options=user_dates, index=len(user_dates) - 1,
    format_func=lambda d: d.strftime("%d/%m/%Y")
)

# Page header
st.title("Step Statistics")
st.caption(f"User {user_id}.{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
st.divider()

# === User overview (moved from sidebar) ===
with st.container(border=True):
    st.markdown("**User Overview**")
    u1, u2, u3, u4 = st.columns(4)
    u1.metric("User Class", user_data["Class"].iloc[0])
    u2.metric("Days Recorded", len(user_data))
    u3.metric("Avg Daily Steps", f"{int(user_data['TotalSteps'].mean()):,}")
    u4.metric("Avg Daily Calories", f"{int(user_data['Calories'].mean()):,}")

st.write("")

# === Main content ===
if start_date > end_date:
    st.warning("Start date must be before end date.")
else:
    # Steps chart
    with st.container(border=True):
        fig_steps = plot_daily_steps(
            user_id=user_id, start_date=start_date, end_date=end_date, df=df_steps
        )
        if fig_steps is not None:
            st.pyplot(fig_steps)

    # Period summary (date-filtered — different from the overall stats above)
    date_filtered = user_data[
        (user_data["ActivityDate"].dt.date >= start_date) &
        (user_data["ActivityDate"].dt.date <= end_date)
    ]

    if not date_filtered.empty:
        with st.container(border=True):
            st.markdown("**Period Summary**")
            st.caption("Totals and averages for the selected date range.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Steps", f"{int(date_filtered['TotalSteps'].sum()):,}")
            c2.metric("Avg Daily Steps", f"{int(date_filtered['TotalSteps'].mean()):,}")
            c3.metric("Avg Calories/Day", f"{int(date_filtered['Calories'].mean()):,}")
            c4.metric("Avg Active Min/Day", f"{int((date_filtered['VeryActiveMinutes'] + date_filtered['FairlyActiveMinutes']).mean()):,}")
    else:
        st.info("No data for this date range.")

    # Group comparison
    avg_steps_all = int(df_overview["TotalSteps"].mean())
    user_avg_steps = int(user_data["TotalSteps"].mean())
    per_user_avgs = df_overview.groupby("Id")["TotalSteps"].mean()
    steps_percentile = (per_user_avgs < user_avg_steps).mean()

    with st.container(border=True):
        st.markdown("**Group Comparison**")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(
            "This user's avg steps",
            f"{user_avg_steps:,}",
            f"{user_avg_steps - avg_steps_all:+,} vs group",
        )
        col_b.metric("Group avg steps", f"{avg_steps_all:,}")
        if steps_percentile >= 0.5:
            col_c.success(f"Above average — top {int((1 - steps_percentile) * 100)}% of users")
        else:
            col_c.info(f"Below average — bottom {int(steps_percentile * 100)}% of users")
