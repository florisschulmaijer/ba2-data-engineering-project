import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import sqlite3

# === Page config ===
st.set_page_config(
    page_title="Heart Rate & Intensity",
    page_icon="fitbit",
    layout="wide",
    initial_sidebar_state="expanded"
)

BG_COLOR = "#111420"
C_RED = "#D62728"
C_BLUE = "#4C9BE8"

def style_ax(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

# Sidebar
st.sidebar.markdown(
    """
    <div style="padding: 12px 4px 8px 4px;">
        <div style="color:white; font-size:1.1rem; font-weight:700; margin-bottom:4px;">Heart Rate & Intensity</div>
        <div style="color:#9B9EAC; font-size:0.78rem; line-height:1.5;">
            Per-user heart rate and exercise intensity over time. Available for 14 of 35 users.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()

# === Data loading ===
@st.cache_data
def load_heart_rate_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM heart_rate", conn)
    conn.close()
    return df

@st.cache_data
def load_intensity_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM hourly_intensity", conn)
    conn.close()
    return df

df_heart_rate       = load_heart_rate_data()
df_hourly_intensity = load_intensity_data()

# Plotting function
def plot_user_HR_exercise_int(user_id, start_date=None, end_date=None,
                               df_1=df_heart_rate, df_2=df_hourly_intensity):
    df_hr = df_1.copy()
    df_hr["Id"]   = df_hr["Id"].astype("int64")
    df_hr["Time"] = pd.to_datetime(df_hr["Time"], format="%m/%d/%Y %I:%M:%S %p")
    df_hr["Hour"] = df_hr["Time"].dt.floor("h")

    df_hr_hourly = (
        df_hr.groupby(["Id", "Hour"])["Value"]
        .mean().reset_index()
        .rename(columns={"Value": "AvgHeartRate"})
    )

    df_intensity = df_2.copy()
    df_intensity["Id"]           = df_intensity["Id"].astype("int64")
    df_intensity["ActivityHour"] = pd.to_datetime(
        df_intensity["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p"
    )
    df_intensity.rename(columns={"ActivityHour": "Hour"}, inplace=True)

    df_merged = pd.merge(df_hr_hourly, df_intensity, on=["Id", "Hour"], how="inner")
    df_user   = df_merged[df_merged["Id"] == user_id].copy()

    if start_date is not None:
        start_dt = pd.to_datetime(start_date)
        end_dt   = pd.to_datetime(end_date) if end_date else start_dt
        df_user  = df_user[
            (df_user["Hour"] >= start_dt) &
            (df_user["Hour"] < end_dt + pd.Timedelta(days=1))
        ]

    if df_user.empty:
        return None

    df_user = df_user.sort_values("Hour")

    fig, ax1 = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG_COLOR)
    style_ax(ax1)
    ax1.grid(True, linestyle="--", linewidth=0.5, alpha=0.3, color="#888")

    line1, = ax1.plot(df_user["Hour"], df_user["AvgHeartRate"],
                      color=C_RED, linewidth=2, label="Avg Heart Rate (bpm)")
    ax1.set_ylabel("Avg Heart Rate (bpm)", color=C_RED)
    ax1.tick_params(axis="y", labelcolor=C_RED)

    ax2 = ax1.twinx()
    ax2.set_facecolor(BG_COLOR)
    ax2.tick_params(colors="white")
    ax2.yaxis.label.set_color("white")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#444")

    line2, = ax2.plot(df_user["Hour"], df_user["TotalIntensity"],
                      color=C_BLUE, linewidth=2, label="Total Intensity")
    ax2.set_ylabel("Total Intensity", color=C_BLUE)
    ax2.tick_params(axis="y", labelcolor=C_BLUE)

    ax1.legend([line1, line2], ["Avg Heart Rate (bpm)", "Total Intensity"],
               loc="upper left", facecolor="#1e2130", labelcolor="white")

    if start_date is None:
        title = f"Heart Rate & Intensity — User {user_id}"
    elif start_date == end_date or end_date is None:
        title = f"Heart Rate & Intensity — User {user_id} on {start_date}"
    else:
        title = f"Heart Rate & Intensity — User {user_id}  |  {start_date} to {end_date}"

    ax1.set_title(title, fontsize=13, fontweight="bold", color="white")
    ax1.set_xlabel("Hour")
    fig.tight_layout()
    return fig

# Sidebar controls
st.sidebar.markdown("**Select a User**")
user_id = st.sidebar.selectbox(
    "User ID",
    [2022484408, 2026352035, 2347167796, 4020332650, 4558609924,
     5553957443, 5577150313, 6117666160, 6391747486, 6775888955,
     6962181067, 7007744171, 8792009665, 8877689391]
)

min_dt = datetime.date(2016, 3, 26)
max_dt = datetime.date(2016, 4, 12)

st.sidebar.divider()
start_date = st.sidebar.date_input("Start date", min_value=min_dt, max_value=max_dt, value=min_dt)
end_date   = st.sidebar.date_input("End date",   min_value=min_dt, max_value=max_dt, value=max_dt)

# Page header
st.title("Heart Rate & Intensity")
st.caption(
    f"**Visual Analysis:** Tracking User {user_id} from {start_date} to {end_date}. "
    "The blue spikes represent exercise or high-movement events, while the red line tracks "
    "how the cardiovascular system responded to those intensity changes."
)
st.divider()

# Chart
with st.container(border=True):
    st.caption("May take a few seconds to render.")
    fig_hr = plot_user_HR_exercise_int(
        user_id=user_id,
        df_1=df_heart_rate,
        df_2=df_hourly_intensity,
        start_date=start_date,
        end_date=end_date
    )
    if fig_hr is not None:
        st.pyplot(fig_hr)
    else:
        st.warning("No data found. Try a different user or broader date range.")
