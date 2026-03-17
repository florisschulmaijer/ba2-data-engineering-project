import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

conn = sqlite3.connect("fitbit_database.db")

activity_query = """
SELECT Id, ActivityDate, VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes, SedentaryMinutes
FROM daily_activity
"""
activity = pd.read_sql_query(activity_query, conn)

activity["ActivityDate"] = pd.to_datetime(activity["ActivityDate"]).dt.normalize()
activity["Id"] = activity["Id"].astype("int64")
activity["TotalActiveMinutes"] = (
    activity["VeryActiveMinutes"]
    + activity["FairlyActiveMinutes"]
    + activity["LightlyActiveMinutes"]
)

sleep_query = """
SELECT Id, logId, date, value
FROM minute_sleep
"""
sleep = pd.read_sql_query(sleep_query, conn)

sleep["date"] = pd.to_datetime(sleep["date"])
sleep["Id"] = sleep["Id"].astype("int64")

sleep_sessions = (
    sleep.groupby(["Id", "logId"])
    .agg(
        sleep_start=("date", "min"),
        sleep_end=("date", "max"),
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

df = df.drop(columns=["sleep_date"])

print(df.head())

model_active = smf.ols(
    "sleep_duration_minutes ~ TotalActiveMinutes",
    data=df
).fit()

print("\nRegression: Sleep Duration vs Total Active Minutes")
print(model_active.summary())

model_sedentary = smf.ols(
    "sleep_duration_minutes ~ SedentaryMinutes",
    data=df
).fit()

print("\nRegression: Sleep Duration vs Sedentary Minutes")
print(model_sedentary.summary())

plt.figure(figsize=(8, 5))
plt.scatter(df["TotalActiveMinutes"], df["sleep_duration_minutes"], alpha=0.4)
plt.xlabel("Total Active Minutes")
plt.ylabel("Sleep Duration (minutes)")
plt.title("Sleep Duration vs Total Active Minutes")

x_vals = pd.Series(sorted(df["TotalActiveMinutes"]))
y_vals = model_active.params.iloc[0] + model_active.params.iloc[1] * x_vals
plt.plot(x_vals, y_vals)

plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 5))
plt.scatter(df["SedentaryMinutes"], df["sleep_duration_minutes"], alpha=0.4)
plt.xlabel("Sedentary Minutes")
plt.ylabel("Sleep Duration (minutes)")
plt.title("Sleep Duration vs Sedentary Minutes")

x_vals = pd.Series(sorted(df["SedentaryMinutes"]))
y_vals = model_sedentary.params.iloc[0] + model_sedentary.params.iloc[1] * x_vals
plt.plot(x_vals, y_vals)

plt.tight_layout()
plt.show()

residuals = model_sedentary.resid

sm.qqplot(residuals, line="45", fit=True)
plt.title("QQ Plot of Residuals, Sleep vs Sedentary Minutes")
plt.tight_layout()
plt.show()

print("\nShapiro-Wilk test for residual normality")
print(stats.shapiro(residuals))

conn.close()