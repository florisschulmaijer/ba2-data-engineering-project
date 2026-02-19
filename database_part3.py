import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.sandbox.distributions.examples.ex_gof import freq

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
# Convert Date to datetime
df_sleep["date"] = pd.to_datetime(df_sleep["date"])
#df_sLeep, contains:
#date = Date and minute of that day within a defined sleep period in mm/dd/yy hh:mm:ss format
#Note: sleep minute data is commonly exported with :30 sec. In this case, the “floor” of the time
#value can be used to convert to whole minutes.
#Example:
#04/20/2018 10:15:30 → 04/20/201810:15:00
#04/20/2018 10:16:30 → 04/20/201810:16:00

# Value = Value indicating the sleep state. 1 = asleep, 2 = restless, 3 = awake
# Log Id = The unique log id in Fitbit’s system for the sleep   record

#Modify Dataframe to count sleep logs per user

df_sleep = (df_sleep.groupby(["Id", "logId"]).
            agg(
    start_date=("date", "min"),#Date sleep period started
    end_date=("date", "max"), #Date sleep period ended
    Duration =("logId", "count") #Duration: sleep duration in mins
).reset_index())
