import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import statsmodels.api as sm

st.title("Sleep Regression Analysis")

conn = sqlite3.connect("fitbit_database.db")

# Load activity
activity = pd.read_sql_query("""
SELECT Id, ActivityDate, VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes, SedentaryMinutes
FROM daily_activity
""", conn)

activity["ActivityDate"] = pd.to_datetime(activity["ActivityDate"]).dt.normalize()
activity["TotalActiveMinutes"] = (
    activity["VeryActiveMinutes"] +
    activity["FairlyActiveMinutes"] +
    activity["LightlyActiveMinutes"]
)

# Load sleep
sleep = pd.read_sql_query("""
SELECT Id, logId, date
FROM minute_sleep
""", conn)

sleep["date"] = pd.to_datetime(sleep["date"])

sleep_sessions = (
    sleep.groupby(["Id", "logId"])
    .agg(
        sleep_start=("date", "min"),
        sleep_duration_minutes=("date", "count")
    )
    .reset_index()
)

sleep_sessions["sleep_date"] = sleep_sessions["sleep_start"].dt.normalize()

sleep_daily = (
    sleep_sessions.groupby(["Id", "sleep_date"])["sleep_duration_minutes"]
    .sum()
    .reset_index()
)

df = activity.merge(
    sleep_daily,
    left_on=["Id", "ActivityDate"],
    right_on=["Id", "sleep_date"],
    how="inner"
)

# Regression
model_active = smf.ols(
    "sleep_duration_minutes ~ TotalActiveMinutes",
    data=df
).fit()

model_sedentary = smf.ols(
    "sleep_duration_minutes ~ SedentaryMinutes",
    data=df
).fit()

# Plot 1
fig1, ax1 = plt.subplots()
ax1.scatter(df["TotalActiveMinutes"], df["sleep_duration_minutes"])
ax1.set_xlabel("Total Active Minutes")
ax1.set_ylabel("Sleep Duration")
ax1.set_title("Sleep vs Active Minutes")

x_vals = pd.Series(sorted(df["TotalActiveMinutes"]))
y_vals = model_active.params.iloc[0] + model_active.params.iloc[1] * x_vals
ax1.plot(x_vals, y_vals)

st.pyplot(fig1)

# Plot 2
fig2, ax2 = plt.subplots()
ax2.scatter(df["SedentaryMinutes"], df["sleep_duration_minutes"])
ax2.set_xlabel("Sedentary Minutes")
ax2.set_ylabel("Sleep Duration")
ax2.set_title("Sleep vs Sedentary Minutes")

x_vals = pd.Series(sorted(df["SedentaryMinutes"]))
y_vals = model_sedentary.params.iloc[0] + model_sedentary.params.iloc[1] * x_vals
ax2.plot(x_vals, y_vals)

st.pyplot(fig2)

# QQ plot
residuals = model_sedentary.resid
fig3 = sm.qqplot(residuals, line="45")
st.pyplot(fig3)

conn.close()