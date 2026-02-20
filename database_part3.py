import sqlite3
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import pearsonr

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


# Define a function that takes an ID as inpput and returns a figure that contains heart rate and total intensity of the exercise taken

query = """
SELECT *
FROM heart_rate
"""

df_HR = pd.read_sql_query(query, conn)
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

# Investigate the relationship between weather factors and activity of individuals
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

#plt.tight_layout()
#plt.show()


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
