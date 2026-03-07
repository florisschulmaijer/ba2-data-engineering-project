import sqlite3
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import pearsonr
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

# === Bullet 1: Investigate Minute Sleep per day ===
# Set up query
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

# === Bullet 2: Analyse whether amount of sleep is related to daily active minutes ===
# Set up query
query = """
SELECT Id, ActivityDate, VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes
FROM daily_activity
"""
df_activity = pd.read_sql_query(query, conn)
print(df_activity.head())
num_unique_users = df_activity["Id"].nunique()
print(f"Number of unique users of activity data: {num_unique_users}")
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

# === Bullet 3: Sedentary vs sleep ===
query = """
SELECT Id, ActivityDate, SedentaryMinutes
FROM daily_activity
"""
df_sedentary = pd.read_sql_query(query, conn)
df_sedentary["Id"] = df_sedentary["Id"].astype("int64")
df_sedentary["ActivityDate"] = pd.to_datetime(df_sedentary["ActivityDate"]).dt.normalize()
df_sedentary = df_sedentary.rename(columns={"ActivityDate": "end_date"})

# Merge sleep duration with sedentary minutes
sleep_sedentary = df_daily_sleep.merge(df_sedentary, on=["Id", "end_date"], how="inner")

# Fit OLS regression with individual fixed effects
# C(Id) = categorical variable to control for individual-level differences in sleep
model_sedentary = smf.ols("Duration ~ SedentaryMinutes + C(Id)", data=sleep_sedentary).fit()
print(model_sedentary.summary())

# Residual normality checks
residual = model_sedentary.resid

plt.figure(figsize=(7,4))
plt.hist(residual, bins=30)
plt.title("Residuals histogram (Sleep vs SedentaryMinutes)")
plt.xlabel("Residual")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

plt.figure(figsize=(6,6))
sm.qqplot(residual, line="45", fit=True)
plt.title("Q-Q plot of residuals")
plt.tight_layout()
plt.show()

# === Bullet 4: 4-hour blocks (steps, calories, sleep) ===
def hour_to_time_block(hour: int) -> str:
    if 0 <= hour < 4: 
        return "0–4"
    if 4 <= hour < 8: 
        return "4–8"
    if 8 <= hour < 12: 
        return "8–12"
    if 12 <= hour < 16: 
        return "12–16"
    if 16 <= hour < 20: 
        return "16–20"
    return "20–24"

time_block_labels = ["0–4", "4–8", "8–12", "12–16", "16–20", "20–24"]

# Steps by time block
df_hourly_steps = pd.read_sql_query("SELECT * FROM hourly_steps", conn)
df_hourly_steps["ActivityHour"] = pd.to_datetime(df_hourly_steps["ActivityHour"])
df_hourly_steps["block"] = df_hourly_steps["ActivityHour"].dt.hour.apply(hour_to_time_block)
steps_by_block = df_hourly_steps.groupby("block")["StepTotal"].mean().reindex(time_block_labels)

plt.figure(figsize=(8,4))
plt.bar(steps_by_block.index, steps_by_block.values)
plt.title("Average steps per 4-hour block")
plt.xlabel("Time block")
plt.ylabel("Average steps")
plt.tight_layout()
plt.show()

# Calories by time block
df_hourly_calories = pd.read_sql_query("SELECT * FROM hourly_calories", conn)
df_hourly_calories["ActivityHour"] = pd.to_datetime(df_hourly_calories["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p")
df_hourly_calories["block"] = df_hourly_calories["ActivityHour"].dt.hour.apply(hour_to_time_block)
calories_by_block = df_hourly_calories.groupby("block")["Calories"].mean().reindex(time_block_labels)

plt.figure(figsize=(8,4))
plt.bar(calories_by_block.index, calories_by_block.values)
plt.title("Average calories per 4-hour block")
plt.xlabel("Time block")
plt.ylabel("Average calories")
plt.tight_layout()
plt.show()

# Sleep (asleep minutes) by time block
df_minute_sleep = pd.read_sql_query("SELECT * FROM minute_sleep", conn)
df_minute_sleep["date"] = pd.to_datetime(df_minute_sleep["date"])
df_minute_sleep["block"] = df_minute_sleep["date"].dt.hour.apply(hour_to_time_block)
df_minute_sleep["day"] = df_minute_sleep["date"].dt.normalize()

# Calculate minutes asleep per day and block for each user 
asleep = df_minute_sleep[df_minute_sleep["value"] == 1]
sleep_person_day_block = (
    asleep.groupby(["Id", "day", "block"])
    .size()
    .reset_index(name="minutes_asleep")
)

# Average minutes asleep per block across all users and days
asleep_minutes_by_block = (
    sleep_person_day_block.groupby("block")["minutes_asleep"]
    .mean()
    .reindex(time_block_labels)
)

plt.figure(figsize=(8, 4))
plt.bar(asleep_minutes_by_block.index, asleep_minutes_by_block.values)
plt.title("Average minutes asleep per 4-hour block")
plt.xlabel("Time block (hours)")
plt.ylabel("Average minutes asleep")
plt.tight_layout()
plt.show()



# === Bullet 5: Define a function that takes an ID as inpput and returns a figure that contains heart rate and total intensity of the exercise taken ===
import pandas as pd
import matplotlib.pyplot as plt
query = """
SELECT *
FROM heart_rate
"""

df_HR = pd.read_sql_query(query, conn)
query = """
SELECT *
FROM hourly_intensity
"""
df_intensity = pd.read_sql_query(query, conn)
def plot_user_HR_exercise_int(user_id, df_1=df_HR, df_2=df_intensity):
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

    df_user = df_merged[df_merged["Id"] == user_id].copy()

    fig, ax1 = plt.subplots(figsize=(12, 6))

    line1, = ax1.plot(
        df_user["Hour"],
        df_user["AvgHeartRate"],
        color="red",
        linewidth=2,
        label="Average Heart Rate"
    )
    ax1.set_ylabel("Average Heart Rate", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    ax2 = ax1.twinx()
    line2, = ax2.plot(
        df_user["Hour"],
        df_user["TotalIntensity"],
        color="blue",
        linewidth=2,
        label="Total Intensity"
    )
    ax2.set_ylabel("Total Intensity", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    ax1.legend([line1, line2], ["Average Heart Rate", "Total Intensity"], loc="upper left")

    ax1.set_title(f"Average Heart Rate and Total Intensity for User {user_id}")
    ax1.set_xlabel("Hour")
    fig.tight_layout()

    return fig

'''
df_HR["Id"] = df_HR["Id"].astype("int64")
df_HR["Time"] = pd.to_datetime(df_HR["Time"], format="%m/%d/%Y %I:%M:%S %p")
df_HR["Hour"] = df_HR["Time"].dt.floor('h')

# Calulate the average heart rate for each hour for each user
df_hr_hourly = (
    df_HR.groupby(["Id", "Hour"])["Value"]
    .mean()
    .reset_index()
)

query = """
SELECT *
FROM hourly_intensity
"""
df_intensity = pd.read_sql_query(query, conn)
df_intensity["Id"] = df_intensity["Id"].astype("int64")
df_intensity["ActivityHour"] = pd.to_datetime(df_intensity["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p")

df_intensity.rename(columns={'ActivityHour': 'Hour'}, inplace=True)

df_int_HR = pd.merge(df_hr_hourly, df_intensity, on=["Id", "Hour"], how="inner")
df_int_HR.rename(columns={'Value': 'AvgHeartRate'}, inplace=True)

def plot_user_HR_exercise_int(id):
    
    df_user = df_int_HR[df_int_HR["Id"] == id].copy()
    fig, ax1 = plt.subplots(figsize=(12, 6))

    line1, = ax1.plot(
        df_user["Hour"], df_user["AvgHeartRate"], color="red", label="Average Heart Rate", linewidth=2
    )
    ax1.set_ylabel("Average Heart Rate", color="red")
    ax1.tick_params(axis='y', labelcolor='red')

    ax2 = ax1.twinx()
    line2, = ax2.plot(
        df_user["Hour"], df_user["TotalIntensity"], color="blue", label="Total Intensity", linewidth=2
    )
    ax2.set_ylabel("Total Intensity", color="blue")
    ax2.tick_params(axis='y', labelcolor='blue')

    handles = [line1, line2]
    labels = ['Average Heart Rate', 'Total Intensity']
    ax1.legend(handles, labels, loc='upper left')

    plt.title(f"Average Heart Rate and Total Intensity for User {id}")
    plt.xlabel("Hour")
    plt.tight_layout()
    plt.show()


#plot_user_HR_exercise_int(8877689391)
'''
# === Bullet 6: Investigate the relationship between weather factors and activity of individuals === 
weather = pd.read_csv("data/ChicagoWeather.csv")
weather['datetime'] = pd.to_datetime(weather['datetime'], format="%Y-%m-%d")
weather = weather[['datetime', 'temp', 'precip', 'windspeed', "feelslike"]]

query = """
SELECT *
FROM daily_activity
"""
df_activity = pd.read_sql_query(query, conn)
df_activity["Id"] = df_activity["Id"].astype("int64")
df_activity["ActivityDate"] = pd.to_datetime(df_activity["ActivityDate"], format="%m/%d/%Y")

# Merge activity with classification df
df_activity = df_activity.merge(df[["Id", "Class"]], on="Id", how="left")

activity_daily = df_activity.groupby("ActivityDate").agg({
    "TotalSteps": "mean",
    "VeryActiveMinutes": "mean",
    "FairlyActiveMinutes": "mean",
    "LightlyActiveMinutes": "mean",
    "SedentaryMinutes": "mean",
    "Calories": "mean",      
    'TotalDistance': 'mean',             
    "ModeratelyActiveDistance": "mean",
    "LightActiveDistance": "mean",     
    "SedentaryActiveDistance": "mean"
}).reset_index()

activity_daily_by_class = df_activity.groupby(["ActivityDate", "Class"]).agg({
        "TotalSteps": "mean",
    "VeryActiveMinutes": "mean",
    "FairlyActiveMinutes": "mean",
    "LightlyActiveMinutes": "mean",
    "SedentaryMinutes": "mean",
    "Calories": "mean",      
    'TotalDistance': 'mean',             
    "ModeratelyActiveDistance": "mean",
    "LightActiveDistance": "mean",     
    "SedentaryActiveDistance": "mean"}).reset_index()

merged_df_weather = activity_daily.merge(weather, left_on="ActivityDate", right_on="datetime", how="left")
merged_df_weather_by_class = activity_daily_by_class.merge(weather, left_on="ActivityDate", right_on="datetime", how="left")

activity_vars = [
    "TotalSteps", "VeryActiveMinutes", "FairlyActiveMinutes",
    "LightlyActiveMinutes", "SedentaryMinutes", "Calories",
    "TotalDistance", "ModeratelyActiveDistance",
    "LightActiveDistance", "SedentaryActiveDistance"
]

weather_vars = ["temp", "precip", "windspeed", 'feelslike']

results = []

for wea in weather_vars:
    for act in activity_vars:
        r, p = pearsonr(merged_df_weather[wea], merged_df_weather[act])
        results.append((wea, act, r, p))

corr_df = pd.DataFrame(results, columns=["weather", "activity", "r", "p"])

r_threshold = 0.25

pairs = corr_df[(corr_df["r"].abs() > r_threshold) & (corr_df["p"] < 0.05)].copy()
print("Meaningful pairs:")
print(pairs)

def annotate_corr(ax, r, p):
    ax.annotate(
        f"r = {r:.2f}\np = {p:.3f}",
        xy=(0.05, 0.85),
        xycoords="axes fraction",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black")
    )

fig, axes = plt.subplots(len(pairs), 1, figsize=(8, 4 * len(pairs)))

for ax, row in zip(axes, pairs.itertuples()):
    wea = row.weather
    act = row.activity
    r = row.r
    p = row.p
    
    sns.regplot(
        data=merged_df_weather,
        x=wea,
        y=act,
        scatter_kws={'alpha':0.4},
        line_kws={'color':'red'},
        ax=ax
    )
    
    ax.set_title(f"Correlation between {wea} and {act}")

    annotate_corr(ax, r, p)

plt.tight_layout()
plt.show()

# Class-wise analysis for weather-activity correlations

activity_vars = [
    ("TotalSteps", "Total Steps"),
    ("FairlyActiveMinutes", "Fairly Active Minutes"),
    ("Calories", "Calories"),
    ("SedentaryMinutes", "Sedentary Minutes")
]

weather_vars = [
    ("temp", "Temperature (°C)"),
    ("precip", "Precipitation (mm)"),
    ("feelslike", "Feels Like (°C)"),
    ("windspeed", "Wind Speed (km/h)")
]

classes = merged_df_weather_by_class["Class"].unique()

palette = {
    "Light": "tab:blue",
    "Moderate": "tab:green",
    "Heavy": "tab:orange"
}

fig, axes = plt.subplots(len(activity_vars), len(weather_vars), figsize=(20, 16))

for i, (act_col, act_label) in enumerate(activity_vars):
    for j, (wea_col, wea_label) in enumerate(weather_vars):
        ax = axes[i, j]

        # scatter background
        sns.scatterplot(
            data=merged_df_weather_by_class,
            x=wea_col,
            y=act_col,
            alpha=0.25,
            color="gray",
            s=20,
            ax=ax
        )

        handles = []

        # LOWESS per class
        for cls in classes:
            subset = merged_df_weather_by_class[merged_df_weather_by_class["Class"] == cls]

            line = sns.regplot(
                data=subset,
                x=wea_col,
                y=act_col,
                lowess=True,
                scatter=False,
                color=palette[cls],
                ax=ax
            )

            # proxy for legend
            proxy = plt.Line2D([0], [0], color=palette[cls], lw=2)
            handles.append((proxy, cls))

        # titles
        if i == 0:
            ax.set_title(wea_label, fontsize=12)
        if j == 0:
            ax.set_ylabel(act_label, fontsize=12)
        else:
            ax.set_ylabel("")

        # legend
        ax.legend(
            handles=[h for h, _ in handles],
            labels=[l for _, l in handles],
            title="Activity Class"
        )

plt.subplots_adjust(
    left=0.06,
    right=0.98,
    top=0.95,
    bottom=0.06,
    wspace=0.25,
    hspace=0.35
)
plt.show()

conn.close()

