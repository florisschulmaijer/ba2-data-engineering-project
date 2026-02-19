import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.sandbox.distributions.examples.ex_gof import freq
import statsmodels.formula.api as smf # Used when providing formula to regression model
import statsmodels.api as sm # Used when manually provide X and y to regression model


# Connect to database
conn = sqlite3.connect("fitbit_database.db")

# See available tables
query = """
SELECT name 
FROM sqlite_master 
WHERE type='table';
"""
tables = pd.read_sql_query(query, conn)
print(tables)

query = """
SELECT Id, COUNT(*) as days
FROM daily_activity
GROUP BY Id;
"""
df = pd.read_sql_query(query, conn)
df["Id"] = df["Id"].astype("int64") # Converts Id from float to int
print(df.head())

def classify(days):
    if days <= 10:
        return "Light"
    elif days <= 15:
        return "Moderate"
    else:
        return "Heavy"

df["Class"] = df["days"].apply(classify)

print(df.head())

conn.close()


# === Part 1: Investigate Minute Sleep per day
# Connect to database
conn = sqlite3.connect("fitbit_database.db")
#Set up query
query = """
SELECT *
FROM minute_sleep
"""
df_sleep = pd.read_sql_query(query, conn)
print(df_sleep.head())
num_unique_users = df_sleep["Id"].nunique()
print(f"Number of unique users of sleep data: {num_unique_users}")
# Convert Date to datetime and ID to category
df_sleep["date"] = pd.to_datetime(df_sleep["date"])
df_sleep["Id"] = df_sleep["Id"].astype("category")
#df_sLeep, contains:
#date = Date and minute of that day within a defined sleep period in mm/dd/yy hh:mm:ss format
#Note: sleep minute data is commonly exported with :30 sec. In this case, the “floor” of the time
#value can be used to convert to whole minutes.
#Example:
#04/20/2018 10:15:30 → 04/20/201810:15:00
#04/20/2018 10:16:30 → 04/20/201810:16:00

# Value = Value indicating the sleep state. 1 = asleep, 2 = restless, 3 = awake
# Log Id = The unique log id in Fitbit’s system for the sleep   record



#=== Df sleep Duration: contains minutes slept per period per user
df_sleep = (df_sleep.groupby(["Id", "logId"]).
            agg(
    start_date=("date", "min"),#Date sleep period started
    end_date=("date", "max"), #Date sleep period ended
    Duration =("logId", "count") #Duration: sleep duration in mins
).reset_index())

#Create new dataframe with sleep minutes per day.
#here, sleep per day is defined as all sleep periods in minutes that ended
#on the same day. SO if someone started sleeping at 10 on 03-25, and woke up at
#03-26, the sleep is counted for the 26th. If someone took a nap on the 26th, the sleep
#duration of that nap is counted for the sleep duration of the 26th.
df_daily_sleep = df_sleep
df_daily_sleep["end_date"] = df_daily_sleep["end_date"].dt.normalize()
df_daily_sleep =  (
    df_daily_sleep.groupby(["Id", "end_date"])["Duration"]
      .sum()
      .reset_index()
)

#Check if no dates occur twice for each participant
duplicates = df_daily_sleep.duplicated(subset=["Id", "end_date"])

if duplicates.any() == True:
    print("Calculating sleep time per day per individual failed")

print(df_daily_sleep.head())
#Sanity checks: check distribution of daily minutes slept
plt.hist(df_daily_sleep["Duration"].apply(lambda x: x/60), bins=20)
plt.xlabel("Sleep Duration in hours")
plt.ylabel("Frequency")
plt.title("Distribution of Daily Sleep Duration")
plt.show()
###
#From the plot, it appears some outliers are visible:
#Some participants slept between 15 and 17 hours, others less than 2.
#Investigate which participants these were, and if this truly reflects the data

outliers = df_daily_sleep[(df_daily_sleep["Duration"] > 900) |
(df_daily_sleep["Duration"] < 120)]
df_sleep["end_date"] = df_sleep["end_date"].dt.normalize()
#filter original frame on outliers
outliers = df_sleep.merge(
    outliers[["Id", "end_date"]],
    on=["Id", "end_date"],
    how="inner")
conn.close()

#==== Part 2: Analyse whether amount of sleep is related to daily active minutes
#connect to database
# Connect to database
conn = sqlite3.connect("fitbit_database.db")
#Set up query
query = """
SELECT Id, ActivityDate, VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes
FROM daily_activity
"""
df_activity = pd.read_sql_query(query, conn)
print(df_activity.head())
num_unique_users = df_activity["Id"].nunique()
print(f"Number of unique users of activity data: {num_unique_users}")
conn.close()
# Convert Date to datetime
df_activity["ActivityDate"] = pd.to_datetime(df_activity["ActivityDate"]).dt.normalize()
df_activity["Id"] = df_activity["Id"].astype("category")
#rename date column for easy merging
df_activity= df_activity.rename(columns = {'ActivityDate':'end_date'})

#create column with total active minutes
df_activity['TotalActiveMin'] = (df_activity['VeryActiveMinutes'] +
                                 df_activity['FairlyActiveMinutes'] +
                                 df_activity['LightlyActiveMinutes'])
print(df_activity.head())

#merge sleep duration with activity df
df_activity = df_activity.merge(
    df_daily_sleep[["Id", "end_date", "Duration"]],
    on=["Id","end_date"],
    how="inner")
print(df_activity.head())

#perform regression for minutes of sleep and active daily minutes
# Multiple Linear regression model, assuming dependence by using
#participant Ids as grouping factors
model_sleep = smf.mixedlm(formula="Duration ~ TotalActiveMin",
                          data=df_activity,
                          groups=df_activity["Id"]).fit()
print(model_sleep.summary())

#Plot regression line for total sleep and total active minutes
#over whole dataset
# Plot scatter
# Plot regression line and scatterplot
plt.figure(figsize=(8,6))
plt.scatter(df_activity["TotalActiveMin"],
         df_activity["Duration"], color="red")

plt.title("Relationship total daily active minutes and sleep duration")
plt.xlabel("Toal active minutes")
plt.ylabel("Sleep duration")
plt.tight_layout()
plt.show()
