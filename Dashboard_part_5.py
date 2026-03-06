import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import sqlite3

from database_part3 import df_activity, df_hourly_steps
from datawrangling_part4 import *
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
#return hourly steps dataframe
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
#call functions
df_heart_rate =load_heart_rate_data()
df_steps = load_hourly_steps_data()
df_activity= load_activity_data()


# === Main Title and Subheaders ===
st.title("FitBit Data In Chicago 2016")
st.header("Summary dashboard for 33 Fitbit Users in Chicago")
st.markdown("This Dashboard shows summary statistics and individual statistics for Fitbit Users in Chicago")
st.subheader("Summary Statistics for All Users")
st.caption("Summaries for activity metrics for all users, based on activity class")

# Streamlit app
st.title("Activity per Weekday, separated by user class")
activity = st.selectbox('Choose Activity Metric', ['TotalSteps'
    ,'TotalDistance','TrackerDistance','VeryActiveDistance','LoggedActivitiesDistance'
    ,'ModeratelyActiveDistance','LightActiveDistance','SedentaryActiveDistance',
    'VeryActiveMinutes','FairlyActiveMinutes','LightlyActiveMinutes','SedentaryMinutes','Calories'])
fig = plot_weekday_activity_per_class(df = df_activity, variable= activity)
#Display figure in pyplot
st.pyplot(fig)



# === Code for the Sidebar ===
st.sidebar.title("Individual Users")
st.sidebar.markdown("Enter your user ID here for individual insights and summaries on specified dates. If you want to only see data from one day, only enter your start date.")
st.sidebar.write("Your User ID: ",)
user_id = st.sidebar.number_input('Enter your user ID', 0, 1503960366)

start_date = st.sidebar.datetime_input("Enter your start date", value = None)
end_date = st.sidebar.datetime_input("Enter your end date", value = None)
st.sidebar.write("Your selected start and end dates:", start_date, end_date)
#display individual summaries in plots
fig_steps = plot_daily_steps(user_id = user_id, start_date = start_date, end_date = end_date, df = df_steps)
#Display figure in pyplot
st.pyplot(fig_steps)
