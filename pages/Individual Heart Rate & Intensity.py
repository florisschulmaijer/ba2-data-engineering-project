import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import sqlite3


st.write("")
#=== Functions to connect to databases and load Data ===
#Note: function to load activity dataframe, returns daily activity dataframe as df activity,
#use df_activity for functions/visualizations where the daily activity dataframe is queried!
@st.cache_data #cache data to ensure faster loading/prevent slow dashboard
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
#load heart rate data
@st.cache_data
def load_heart_rate_data(database="fitbit_database.db"):
    conn = sqlite3.connect("fitbit_database.db")
    query = "SELECT * FROM heart_rate"
    df_heartrate = pd.read_sql_query(query, conn)
    conn.close()
    return df_heartrate
@st.cache_data
def load_intensity_data(database="fitbit_database.db"):
    conn = sqlite3.connect("fitbit_database.db")
    query = "SELECT * FROM hourly_intensity"
    df_hourly_intensity = pd.read_sql_query(query, conn)
    conn.close()
    return df_hourly_intensity

#call functions
df_heart_rate =load_heart_rate_data()
df_steps = load_hourly_steps_data()
df_activity= load_activity_data()
df_hourly_intensity = load_intensity_data()


def plot_user_HR_exercise_int(
        user_id,
        start_date=None,
        end_date=None,
        df_1=df_heart_rate,
        df_2=df_hourly_intensity
    ):

    # -----------------------------
    # ORIGINAL PREPROCESSING (UNCHANGED)
    # -----------------------------
    df_hr = df_1.copy()
    df_hr["Id"] = df_hr["Id"].astype("int64")
    df_hr["Time"] = pd.to_datetime(df_hr["Time"], format="%m/%d/%Y %I:%M:%S %p")
    df_hr["Hour"] = df_hr["Time"].dt.floor("h")

    df_hr_hourly = (
        df_hr.groupby(["Id", "Hour"])["Value"]
        .mean()
        .reset_index()
        .rename(columns={"Value": "AvgHeartRate"})
    )

    df_intensity = df_2.copy()
    df_intensity["Id"] = df_intensity["Id"].astype("int64")
    df_intensity["ActivityHour"] = pd.to_datetime(
        df_intensity["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p"
    )
    df_intensity.rename(columns={"ActivityHour": "Hour"}, inplace=True)

    df_merged = pd.merge(
        df_hr_hourly, df_intensity, on=["Id", "Hour"], how="inner"
    )

    # -----------------------------
    # DATE FILTERING (NEW)
    # -----------------------------
    df_user = df_merged[df_merged["Id"] == user_id].copy()

    if start_date is not None:
        start_date_dt = pd.to_datetime(start_date)
        if end_date is None:
            end_date_dt = start_date_dt
        else:
            end_date_dt = pd.to_datetime(end_date)

        df_user = df_user[
            (df_user["Hour"] >= start_date_dt) &
            (df_user["Hour"] < end_date_dt + pd.Timedelta(days=1))
        ]

    if df_user.empty:
        print("No data found for this user/date range")
        return

    df_user = df_user.sort_values("Hour")

    # -----------------------------
    # VISUAL IMPROVEMENTS (NEW)
    # -----------------------------
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Add grid
    ax1.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

    # Heart rate line
    line1, = ax1.plot(
        df_user["Hour"],
        df_user["AvgHeartRate"],
        color="#D62728",
        linewidth=2.5,
        label="Average Heart Rate"
    )
    ax1.set_ylabel("Average Heart Rate", color="#D62728")
    ax1.tick_params(axis="y", labelcolor="#D62728")

    # Intensity line
    ax2 = ax1.twinx()
    line2, = ax2.plot(
        df_user["Hour"],
        df_user["TotalIntensity"],
        color="#1F77B4",
        linewidth=2.5,
        label="Total Intensity"
    )
    ax2.set_ylabel("Total Intensity", color="#1F77B4")
    ax2.tick_params(axis="y", labelcolor="#1F77B4")

    # Legend
    ax1.legend([line1, line2], ["Average Heart Rate", "Total Intensity"], loc="upper left")

    # Title
    if start_date is None:
        title = f"Average Heart Rate and Total Intensity for User {user_id}"
    elif start_date == end_date or end_date is None:
        title = f"HR & Intensity for User {user_id} on {start_date}"
    else:
        title = f"HR & Intensity for User {user_id} from {start_date} to {end_date}"

    ax1.set_title(title, fontsize=14, fontweight="bold")
    ax1.set_xlabel("Hour")

    fig.tight_layout()
    return fig


st.title("Individual User Heart Rate & Exercise Intensity")

# === Code for the Sidebar ===
st.sidebar.title("Individual Users")
st.sidebar.markdown("Enter your user ID here for individual insights about heart rate and exercise intensity. Recommend to choose start date from 1st of April as March data might be inconsistent")
user_id = st.sidebar.selectbox('Choose a User ID', [2022484408, 2026352035, 2347167796, 4020332650, 4558609924,
       5553957443, 5577150313, 6117666160, 6391747486, 6775888955,
       6962181067, 7007744171, 8792009665, 8877689391])

min_dt = datetime.datetime(2016, 3, 26, 0, 0)
max_dt = datetime.datetime(2016, 4, 12, 23, 59)

start_date = st.sidebar.datetime_input(
    "Start datetime",
    min_value=min_dt,
    max_value=max_dt,
    value=min_dt
)

end_date = st.sidebar.datetime_input(
    "End datetime",
    min_value=min_dt,
    max_value=max_dt,
    value=max_dt
)

st.sidebar.write("Your selected start and end dates:", start_date, end_date)
st.caption("Invidual heart rate and exercise intensity overtime. This might take a little while to run")
fig_heartrate_intensity = plot_user_HR_exercise_int(user_id=user_id, df_1=df_heart_rate, df_2=df_hourly_intensity, start_date=start_date, end_date=end_date)
st.pyplot(fig_heartrate_intensity)