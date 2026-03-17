import sqlite3
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates #used to convert time labels to relevant plot labels
import seaborn as sns
import numpy as np
from scipy.stats import pearsonr

# Dashboard theme
BG_COLOR = "#111420"
C_BLUE = "#4C9BE8"
C_ORANGE = "#E8834C"
C_GREEN = "#52C97A"
C_RED = "#D62728"
C_GRAY = "#9B9EAC"
C_PURPLE = "#A78BFA"

def _style_ax(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

# Connect to database
conn = sqlite3.connect("fitbit_database.db")

# === Bullet 1: Looking for missing values in weight_log and replace them ===
query = '''SELECT * FROM weight_log'''
df = pd.read_sql_query(query, conn)
df.loc[df["WeightKg"].isna(), "WeightKg"] = (
    df.loc[df["WeightKg"].isna(), "WeightPounds"] * 0.45359237
)
df = df.drop('Fat', axis=1)

# === Bullet 2: Merging tables, and look into relationships between variables ===
query = ''' select s1.Id, s1.ActivityHour, s1.Calories, s2.TotalIntensity, s2.AverageIntensity from hourly_calories s1 inner join hourly_intensity s2 on s1.Id = s2.Id and s1.ActivityHour = s2.ActivityHour'''
calories_intensity_df = pd.read_sql_query(query, conn)
calories_intensity_df["Id"] = calories_intensity_df["Id"].astype("Int64")
calories_intensity_df["ActivityHour"] = pd.to_datetime(
    calories_intensity_df["ActivityHour"],
    format="%m/%d/%Y %I:%M:%S %p")
calories_intensity_df["Date"] = calories_intensity_df["ActivityHour"].dt.date
calories_intensity_df = calories_intensity_df.rename(columns={'TotalIntensity_x':'TotalIntensity', 'AverageIntensity_x':'AverageIntensity'})

daily_df = calories_intensity_df.groupby("Date").agg({
    "Calories": "mean",
    "TotalIntensity": "mean",
    "AverageIntensity": "mean"
}).reset_index()

def plot_daily_calories_intensity(df):
    plt.figure(figsize=(12,6))

    plt.plot(df["Date"], df["Calories"], label="Daily Calories", color="red", linewidth=2)
    plt.plot(df["Date"], df["TotalIntensity"], label="Daily Total Intensity", color="blue", linewidth=2)

    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.title("Daily Calories and Intensity")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Relationship between calories and exercise intensity
plot_daily_calories_intensity(daily_df)

# Scatter plot for minutes sleep and daily steps
query = ''' select * from hourly_steps'''
daily_steps = pd.read_sql_query(query, conn)
daily_steps["Date"] = pd.to_datetime(daily_steps["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p").dt.date

daily_steps = daily_steps.groupby(["Id", "Date"])["StepTotal"].sum().reset_index()
query = ''' select * from minute_sleep'''
daily_sleep = pd.read_sql_query(query, conn)
daily_sleep = daily_sleep.copy()
daily_sleep["Date"] = pd.to_datetime(daily_sleep["date"], format="%m/%d/%Y %I:%M:%S %p").dt.date

daily_sleep = daily_sleep.groupby(["Id", "Date"])["value"].sum().reset_index()
steps_sleep = daily_steps.merge(
    daily_sleep,
    on=["Id", "Date"],
    how="inner"
)
plt.figure(figsize=(12,6))

plt.scatter(steps_sleep["StepTotal"], steps_sleep["value"], alpha=0.6)

plt.xlabel("Steps per Day")
plt.ylabel("Minutes Asleep per Night")
plt.title("Daily Steps vs. Sleep Duration")
plt.grid(True)
plt.tight_layout()
plt.show()

# === Bullet 3: Create functions for graphical and statistical summaries for individuals. ===
# connect to database
conn = sqlite3.connect("fitbit_database.db")
query = "SELECT * FROM daily_activity"
df = pd.read_sql_query(query, conn)
conn.close()
# Plot bar graph that shows active distance per day or date range
def plot_total_distance(user_id, start_date=None, end_date=None, df=df):
    # Convert types to correct form
        df["Id"] = df["Id"].astype("Int64")
        df["ActivityDate"] = pd.to_datetime(df["ActivityDate"], format="%m/%d/%Y %I:%M:%S %p")
        # Filter data for user ID
        user_data = df[df["Id"] == user_id].copy()

        # Handle single-day case
        if start_date is not None and end_date is None:
            #start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = start_date

        # Filter date range
        if start_date is not None and end_date is not None:
            #start_date = dt.datetime.strptime(str(start_date), "%Y-%m-%d")
            #end_date = dt.datetime.strptime(str(end_date), "%Y-%m-%d")

            user_data = user_data[
                (user_data["ActivityDate"] >= start_date) &
                (user_data["ActivityDate"] <= end_date)
                ]

        if user_data.empty:
            print("No data available for this selection")
            return None

        # Sort values
        user_data = user_data.sort_values("ActivityDate")

        # Format date for plotting
        user_data["ActivityDate"] = user_data["ActivityDate"].dt.strftime("%Y-%m-%d")

        # Select columns
        user_data = user_data[
            ["ActivityDate", "VeryActiveDistance", "ModeratelyActiveDistance", "LightActiveDistance"]
        ]

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        user_data.plot(
            x="ActivityDate",
            kind="bar",
            stacked=True,
            ax=ax,
            title=f"Total Distance for (User {user_id})"
        )

        ax.set_xlabel("Date")
        ax.set_ylabel("Total Distance")
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

# === Create function to plot daily HR per user ===
# Connect to database
conn = sqlite3.connect("fitbit_database.db")
query = "SELECT * FROM heart_rate"
df = pd.read_sql_query(query, conn)
conn.close()

def plot_daily_HR(user_id, start_date, end_date=None, df = df):
    # Convert types to correct form
    df["Id"] = df["Id"].astype("Int64")
    df["Time"] = pd.to_datetime(df["Time"], format="%m/%d/%Y %I:%M:%S %p")
    start_date_string = start_date
    end_date_string = end_date
    if end_date is None:
        end_date = start_date # Filter on only one date when only one day is given

    # Check if user id exists in frame
    if user_id not in df["Id"].values:
        print("ID not found")
        return

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    # If date filtering requested
    if start_date and end_date:

        # Convert to datetime
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter using datetime range
        user_data = user_data[
            (user_data["Time"] >= start_date) &
            (user_data["Time"] < end_date + pd.Timedelta(days=1))
        ]

        if user_data.empty:
            print("No data in selected date range")
            return

    # Sort chronologically
    user_data = user_data.sort_values("Time")
    if start_date == end_date: #check if only one day is entered, show daily summary
        # Plot data in linegraph for one day
        #Compute max and min HR per day, for plotting later
        # Get row with max heart rate
        max_row = user_data.loc[user_data["Value"].idxmax()]
        # Get row with min heart rate
        min_row = user_data.loc[user_data["Value"].idxmin()]

        # Create a summary DataFrame
        hr_summary = pd.DataFrame({
            "Type": ["Max", "Min"],
            "HeartRate": [max_row["Value"], min_row["Value"]],
            "Time": [max_row["Time"], min_row["Time"]],
            "Hour": [max_row["Time"].hour, min_row["Time"].hour]
        })

        plt.figure(figsize=(12, 6))
        plt.plot(user_data["Time"], user_data["Value"])
        # Format x-axis to show hours only
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator())
        plt.xlabel("Hour of Day")
        plt.ylabel("Heart Rate")
        plt.title(f"Heart Rate by Hour for User {user_id} on {start_date_string}" )
        plt.xticks(rotation=45)
        plt.tight_layout()
        #Add min and max values
        for _, row in hr_summary.iterrows():
            plt.annotate(f"{row['Type']}: {row['HeartRate']}",
                         xy=(row["Time"], row["HeartRate"]),
                         xytext=(0, 10), textcoords='offset points',
                         arrowprops=dict(arrowstyle="->", color='red'))
        plt.show()

    #
    else:
        # Resample / group by hourly intervals to enhance visualization
        user_data = user_data.set_index("Time")
        hr_agg = user_data["Value"].resample("h").mean()
        plt.figure(figsize=(12, 6))
        plt.plot(hr_agg.index, hr_agg.values, marker="o")
        plt.title(f"Hourly Heart Rate for User {user_id} between {start_date_string} and {end_date_string}")
        plt.xlabel("Date")
        plt.ylabel("Heart Rate")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

plot_daily_HR(2022484408,  start_date="2016-04-02")
plot_daily_HR(2022484408,  "2016-04-01", "2016-04-02")

#load data
#connect to database
conn = sqlite3.connect("fitbit_database.db")
query = "SELECT * FROM hourly_steps"
df = pd.read_sql_query(query, conn)
conn.close()

def plot_daily_steps(user_id, start_date, end_date=None, df=df):
    # Convert types to correct form
    df["Id"] = df["Id"].astype("Int64")
    df["Time"] = df["ActivityHour"]
    df["Time"] = pd.to_datetime(df["Time"], format="%m/%d/%Y %I:%M:%S %p")
    start_date_string = start_date
    end_date_string = end_date
    if end_date is None:
        end_date = start_date  # filter on only one date when only one day is given

    # check if user id exists in frame
    if user_id not in df["Id"].values:
        print("ID not found")
        return

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    # If date filtering requested
    if start_date and end_date:

        # Convert to datetime
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter using datetime range
        user_data = user_data[
            (user_data["Time"] >= start_date) &
            (user_data["Time"] < end_date + pd.Timedelta(days=1))
            ]

        if user_data.empty:
            print("No data in selected date range")
            return

    # Sort chronologically
    user_data = user_data.sort_values("Time")
    #if only one day is entered
    if start_date == end_date:

        max_row = user_data.loc[user_data["StepTotal"].idxmax()]
        min_row = user_data.loc[user_data["StepTotal"].idxmin()]

        st_summary = pd.DataFrame({
            "Type": ["Max", "Min"],
            "StepTotal": [max_row["StepTotal"], min_row["StepTotal"]],
            "Time": [max_row["Time"], min_row["Time"]],
        })

        user_data = user_data.set_index("Time")
        st_agg = user_data["StepTotal"].resample("h").mean()

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor(BG_COLOR)
        _style_ax(ax)

        ax.bar(st_agg.index, st_agg.values, width=pd.Timedelta(minutes=55),
               color=C_BLUE, edgecolor=BG_COLOR)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
        ax.xaxis.set_major_locator(mdates.HourLocator())

        ax.set_xlabel("Hour")
        ax.set_ylabel("Steps per Hour")
        ax.set_title(f"Steps per Hour for User {user_id} on {start_date_string}")

        for _, row in st_summary.iterrows():

            if row["Type"] == "Max":
                offset = 10
                va = "bottom"
            else:
                offset = -15
                va = "top"

            ax.annotate(
                f"{row['Type']}: {row['StepTotal']}",
                xy=(row["Time"], row["StepTotal"]),
                xytext=(0, offset),
                textcoords='offset points',
                ha='center',
                va=va,
                color="white",
                arrowprops=dict(arrowstyle="->", color=C_ORANGE)
            )

    else:
    #for multiple days
        max_row = user_data.loc[user_data["StepTotal"].idxmax()]
        min_row = user_data.loc[user_data["StepTotal"].idxmin()]

        st_summary = pd.DataFrame({
            "Type": ["Max", "Min"],
            "StepTotal": [max_row["StepTotal"], min_row["StepTotal"]],
            "Time": [max_row["Time"], min_row["Time"]],
        })

        user_data = user_data.set_index("Time")
        st_agg = user_data["StepTotal"].resample("4h").sum()

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor(BG_COLOR)
        _style_ax(ax)

        ax.bar(st_agg.index, st_agg.values, width=pd.Timedelta(hours=3.5),
               color=C_BLUE, edgecolor=BG_COLOR)

        ax.set_xlabel("Date")
        ax.set_ylabel("Steps per 4 Hours")
        ax.set_title(
            f"Steps per 4 Hours for User {user_id} between {start_date_string} and {end_date_string}"
        )

        for _, row in st_summary.iterrows():

            if row["Type"] == "Max":
                offset = 10
                va = "bottom"
            else:
                offset = -15
                va = "top"

            ax.annotate(
                f"{row['Type']}: {row['StepTotal']}",
                xy=(row["Time"], row["StepTotal"]),
                xytext=(0, offset),
                textcoords='offset points',
                ha='center',
                va=va,
            )

    return fig
plot_daily_steps(2022484408, start_date="2016-04-02", df = df)
plot_daily_steps(2022484408, start_date="2016-04-02", end_date="2016-04-06", df = df)

#=== define function for plotting HR, sleep duration and sleep value per user
# def individual_sleep(date, userid, database = ):

# Set up query
conn = sqlite3.connect("fitbit_database.db")
query = """
SELECT *
FROM minute_sleep
"""
df_sleep = pd.read_sql_query(query, conn)
# Convert Date to datetime and ID to category
df_sleep["date"] = pd.to_datetime(df_sleep["date"])
df_sleep["Id"] = df_sleep["Id"].astype("category")
#merge heart rate and sleep data
query = """
SELECT *
FROM heart_rate
"""
df_HR = pd.read_sql_query(query, conn)
# Convert Date to datetime and ID to category
df_HR["Time"] = pd.to_datetime(df_HR["Time"])
df_HR["Id"] = df_HR["Id"].astype("category")

#merge dataframes and rename columns
df_merged = pd.merge(
    df_sleep,
    df_HR,
    left_on=['date', 'Id'],
    right_on=['Time', 'Id'],
    how='inner'
)
df_merged["sleep_value"] =df_merged["value"]
df_merged["HR"] =df_merged["Value"]
df = df_merged[["Id", "sleep_value", "HR", "Time", "logId"]]

#define function that plots heart rate and sleep values for individual users on a given day
def plot_sleep_HR(user_id, start_date, df):

    df = df.copy()
    df["Time"] = pd.to_datetime(df["Time"])

    start_date_string = start_date
    start_date = pd.to_datetime(start_date)

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    # Filter for the selected day
    # Expand search window to include sleep before midnight
    sleep_day_start = start_date - pd.Timedelta(hours=6) #define sleep day as 18:00 to 18:00


    user_data = user_data[
        (user_data["Time"] >= sleep_day_start) &
        (user_data["Time"] < sleep_day_start + pd.Timedelta(days=1))
        ]
    print("User:", user_id)
    print("Rows for user:", len(df[df["Id"] == user_id]))
    print("Rows in time window:", len(user_data))
    if user_data.empty:
        print("No data in selected date range")
        return
    #Select longest sleep session, exclude naps
    session_lengths = user_data.groupby("logId")["Time"].count()
    longest_session = session_lengths.idxmax()

    user_data = user_data[user_data["logId"] == longest_session]

    # Sort chronologically
    user_data = user_data.sort_values("Time")

    user_data = user_data.sort_values("Time")
    fig, ax1 = plt.subplots(figsize=(12,6))

    # Color mapping for sleep stages
    colors = {
        1: "blue",      # asleep
        2: "green",    # restless
        3: "orange"        # awake
    }

    # Plot bars for sleep stages
    for stage, color in colors.items():
        stage_data = user_data[user_data["sleep_value"] == stage]
        ax1.bar(
            stage_data["Time"],
            stage_data["sleep_value"],
            width=pd.Timedelta(minutes=5),
            color=color,
            label=f"{stage}"
        )

    ax1.set_ylabel("Sleep Value")

    # Heart rate axis
    ax2 = ax1.twinx()
    ax2.plot(
        user_data["Time"],
        user_data["HR"],
        color="black",
        linewidth=2,
        label="Heart Rate"
    )
    ax2.set_ylabel("Heart Rate (bpm)")

    # Time formatting: every 40 minutes
    ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    ax1.set_xlabel("Time")

    ax1.set_title(f"Sleep and Heart Rate for User {user_id} around {start_date_string}")

    # Custom legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor='blue', label='Sleep Value 1 = Asleep'),
        Patch(facecolor='green', label='Sleep Value 2 = Restless'),
        Patch(facecolor='orange', label='Sleep Value 3 = Awake')
    ]

    ax1.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0
    )

    fig.tight_layout(rect=[0, 0, 0.85, 1])
    fig.tight_layout()

    return fig
#%%
#plot_sleep_HR(user_id = 2347167796	, start_date = "2016-03-29", df = df)


###add function to show pie chart of sleep efficiency for given user
#%%
def plot_sleep_summary_HR(user_id, start_date, df=df):

    df["Id"] = df["Id"].astype("Int64")
    df["Time"] = pd.to_datetime(df["Time"])

    start_date_string = start_date
    start_date = pd.to_datetime(start_date)

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    # Define sleep day window (18:00–18:00)
    sleep_day_start = start_date - pd.Timedelta(hours=6)

    user_data = user_data[
        (user_data["Time"] >= sleep_day_start) &
        (user_data["Time"] < sleep_day_start + pd.Timedelta(days=1))
    ]

    if user_data.empty:
        print("No data in selected date range")
        return

    # Select longest sleep session
    session_lengths = user_data.groupby("logId")["Time"].count()
    longest_session = session_lengths.idxmax()

    user_data = user_data[user_data["logId"] == longest_session]

    # Sleep stage labels
    stage_labels = {
        1: "Asleep",
        2: "Restless",
        3: "Awake"
    }

    colors = {
        1: "blue",
        2: "green",
        3: "orange"
    }

    # Count sleep stages
    stage_counts = user_data["sleep_value"].value_counts().sort_index()

    labels = [stage_labels[s] for s in stage_counts.index]
    pie_colors = [colors[s] for s in stage_counts.index]

    # ---- Sleep metrics ----
    asleep_count = stage_counts.get(1, 0)
    total_count = stage_counts.sum()

    sleep_efficiency = (asleep_count / total_count) * 100 if total_count > 0 else 0

    # get average heart rate
    avg_hr = int(user_data["HR"].mean())
    min_hr = user_data["HR"].min()
    max_hr = user_data["HR"].max()

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(7,6))

    ax.pie(
        stage_counts,
        labels=labels,
        colors=pie_colors,
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title(f"Sleep Summary for User {user_id} on {start_date_string}")

    # ---- Metrics box ----
    metrics_text = (
        f"Average HR: {avg_hr} bpm\n"
        f"Min HR: {min_hr} bpm\n"
        f"Max HR: {max_hr} bpm\n"
        f"Sleep Efficiency: {sleep_efficiency:.1f}%"
    )

    ax.text(
        1.2, -0.9,
        metrics_text,
        fontsize=11,
        bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.5")
    )

    plt.tight_layout()

    return fig


#==== plotting function for when heart rate data is not availaible
#bar chart that shows actual sleep, true sleep minutes and hours slept
def plot_sleep(user_id, start_date, df):

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    start_date_string = start_date
    start_date = pd.to_datetime(start_date)

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    # Define sleep day window (18:00 to 18:00)
    sleep_day_start = start_date - pd.Timedelta(hours=6)

    user_data = user_data[
        (user_data["date"] >= sleep_day_start) &
        (user_data["date"] < sleep_day_start + pd.Timedelta(days=1))
    ]



    if user_data.empty:
        print("No data in selected date range")
        return

    # Select longest sleep session (exclude naps)
    session_lengths = user_data.groupby("logId")["date"].count()
    longest_session = session_lengths.idxmax()

    user_data = user_data[user_data["logId"] == longest_session]

    # Sort chronologically
    user_data = user_data.sort_values("date")

    fig, ax = plt.subplots(figsize=(14,6))
    fig.patch.set_facecolor(BG_COLOR)
    _style_ax(ax)

    # Color mapping for sleep stages
    colors = {
        1: C_BLUE,
        2: C_ORANGE,
        3: C_RED
    }

    # Plot bars for sleep stages
    for stage, color in colors.items():
        stage_data = user_data[user_data["value"] == stage]
        ax.bar(
            stage_data["date"],
            stage_data["value"],
            width=pd.Timedelta(minutes=1),
            color=color,
            label=f"{stage}"
        )

    ax.set_ylabel("Sleep Value")

    # Time formatting
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    ax.set_xlabel("Time")
    ax.set_title(f"Sleep Stages for User {user_id} around {start_date_string}")
    plt.xticks(rotation=45)
    # Custom legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=colors[1], label='Sleep Value 1 = Asleep'),
        Patch(facecolor=colors[2], label='Sleep Value 2 = Restless'),
        Patch(facecolor=colors[3], label='Sleep Value 3 = Awake')
    ]

    ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0,
        facecolor="#1e2130",
        labelcolor="white"
    )

    fig.tight_layout(rect=[0, 0, 0.85, 1])

    return fig

def plot_sleep_summary(user_id, start_date, df=df):

    df["Id"] = df["Id"].astype("Int64")
    df["date"] = pd.to_datetime(df["date"])

    start_date_string = start_date
    start_date = pd.to_datetime(start_date)

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    # Define sleep day window (18:00–18:00)
    sleep_day_start = start_date - pd.Timedelta(hours=6)

    user_data = user_data[
        (user_data["date"] >= sleep_day_start) &
        (user_data["date"] < sleep_day_start + pd.Timedelta(days=1))
    ]

    if user_data.empty:
        print("No data in selected date range")
        return

    # Select longest sleep session
    session_lengths = user_data.groupby("logId")["date"].count()
    longest_session = session_lengths.idxmax()

    user_data = user_data[user_data["logId"] == longest_session]

    # Sleep stage labels
    stage_labels = {
        1: "Asleep",
        2: "Restless",
        3: "Awake"
    }

    colors = {
        1: C_BLUE,
        2: C_ORANGE,
        3: C_RED
    }

    # Count stages
    stage_counts = user_data["value"].value_counts().sort_index()

    # Convert to minutes (assuming 5-minute epochs)
    stage_minutes = stage_counts * 1

    # Sleep metrics
    asleep_minutes = stage_minutes.get(1, 0)
    total_minutes = stage_minutes.sum()
    total_hours = total_minutes/60

    sleep_efficiency = (asleep_minutes / total_minutes) * 100 if total_minutes > 0 else 0

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(9,3))
    fig.patch.set_facecolor(BG_COLOR)
    _style_ax(ax)

    left = 0
    for stage in stage_minutes.index:
        minutes = stage_minutes[stage]

        ax.barh(
            y=0,
            width=minutes,
            left=left,
            color=colors[stage],
            label=f"{stage_labels[stage]} ({minutes} min)"
        )

        left += minutes

    ax.set_xlim(0, total_minutes)
    ax.set_yticks([])
    ax.set_xlabel("Minutes")
    ax.set_title(f"Sleep Summary for User {user_id} on {start_date_string}")

    # Legend
    ax.legend(
        title="Sleep Stages",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        facecolor="#1e2130",
        labelcolor="white",
        title_fontsize=9
    )

    # Metrics box
    metrics_text = (
        f"Total Sleep Window: {total_minutes} min\n"
        f"Asleep: {asleep_minutes} min\n"
        f"Sleep Efficiency: {sleep_efficiency:.1f}%\n"
        f"Total Sleep in Hours: {total_hours:.1f} hours\n"
    )

    ax.text(
        1.02, -0.4,
        metrics_text,
        transform=ax.transAxes,
        fontsize=10,
        color="white",
        bbox=dict(facecolor="#191d2e", edgecolor="#444", boxstyle="round,pad=0.5")
    )

    plt.tight_layout()

    return fig
#function that shows bar charts of total average sleep per weekday for individual users
def plot_sleep_overview(user_id, df):
    # Filter for user
    user_data = df[df["Id"] == user_id].copy()
    #calculate sleep durations for each log id
    df_user_sleep = (user_data.groupby(["logId"]).
                     agg(
        start_date=("date", "min"),  # Date sleep period started
        end_date=("date", "max"),  # Date sleep period ended
        Duration=("logId", "count")  # Duration: sleep duration in mins
    ).reset_index())
    df_user_sleep["Duration"] = df_user_sleep["Duration"]/60
    df_user_sleep= df_user_sleep.round({"Duration": 2}) #round hours to two decimals for plotting
    #Add columns with days of the week and whether there are naps or not
    df_user_sleep["DayOfWeek"] = df_user_sleep["start_date"].dt.day_name()
    df_user_sleep["DayOfWeek"] = df_user_sleep["DayOfWeek"].astype("category")
    #classify nap as <4 hours sleep
    df_user_sleep["Sleep Type"] = df_user_sleep["Duration"].apply(lambda x: "Nap" if (x < 4) else "Full Night").astype(
        "category")
    total_naps = len(df_user_sleep[df_user_sleep['Sleep Type']=='Nap'])
    average_sleep_hours = df_user_sleep[df_user_sleep['Sleep Type']=='Full Night']["Duration"].mean()

    #plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax = sns.barplot(df_user_sleep, x="DayOfWeek", y="Duration", hue="Sleep Type",
                order=["Monday", "Tuesday", "Wednesday", "Thursday",
                       "Friday", "Saturday", "Sunday"],
                palette={"Full Night": C_BLUE, "Nap": C_ORANGE},
                estimator="mean", errorbar=None)
    _style_ax(ax)
    for container in ax.containers:
        labels = [f"{v:.2f}" for v in container.datavalues]
        ax.bar_label(container, labels=labels, fontsize=10, color="white")

    # Metrics box
    metrics_text = (
        f"Full night sleep average:{average_sleep_hours:.1f}\n"
        f"Total number of naps:{total_naps}\n"
        "Naps are defined as sleep periods\n"
        "lasting less than 4 hours"
    )

    ax.text(
        1.02, -0.4,
        metrics_text,
        transform=ax.transAxes,
        fontsize=10,
        color="white",
        bbox=dict(facecolor="#191d2e", edgecolor="#444", boxstyle="round,pad=0.5")
    )

    plt.tight_layout()

    ax.set_xlabel("Day of the week")
    ax.set_ylabel("Average Daily Sleep Duration in Hours")
    ax.set_title(f'Hours slept on average per weekday for {user_id}')
    ax.legend(title="Sleep Type", facecolor="#1e2130", labelcolor="white")
    return fig


#=== Complete Datasetlevel summaries ===
# connect to database
conn = sqlite3.connect("fitbit_database.db")
query = "SELECT * FROM daily_activity"
df = pd.read_sql_query(query, conn)
conn.close()
#plot distribution of steps per weekday for each user class (heavy, light, moderate)
def plot_weekday_activity_per_class(df,
                                    variable="TotalDistance"):

    # Convert types to correct form
    df["Id"] = df["Id"].astype("Int64")
    df.rename(columns={'ActivityDate': 'Time'}, inplace=True)
    df["Time"] = pd.to_datetime(df["Time"], format="%m/%d/%Y")
    #Add column with class of the user
    df['Class'] = df.groupby('Id')['Id'].transform('count')
    #use classify function to mutate column
    def classify(days):
        if days <= 10:
            return "Light"
        elif days <= 15:
            return "Moderate"
        else:
            return "Heavy"

    df["Class"] = df["Class"].apply(classify)
    df["Class"] = df["Class"].astype("category")
    #Add column with day of the week
    # Get day of the week for each activity date
    df["DayOfWeek"] = df["Time"].dt.day_name()
    df["DayOfWeek"] = df["DayOfWeek"].astype("category")

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_COLOR)

    # Create the boxplot on the axis
    sns.boxplot(data=df, x="DayOfWeek", y=variable, hue="Class",
                order=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                hue_order=["Light", "Moderate", "Heavy"],
                palette={"Light": C_BLUE, "Moderate": C_ORANGE, "Heavy": C_GREEN},
                ax=ax)
    _style_ax(ax)

    ax.set_xlabel("Day of the week")
    ax.set_ylabel(variable)
    ax.set_title(f'Distribution of {variable} per weekday and user class')
    ax.legend(title="User Class", facecolor="#1e2130", labelcolor="white")
    # --- SUMMARY STATISTICS ---
    var_series = df[variable].dropna()

    min_val = var_series.min()
    max_val = var_series.max()
    median_val = var_series.median()

    conclusion = (
        f"For **{variable}**, the minimum observed value is **{min_val:.2f}**, "
        f"the maximum is **{max_val:.2f}**, and the median is **{median_val:.2f}** "
        f"across all participants and weekdays."
    )

    return fig, conclusion

#Generate some plots
plot_weekday_activity_per_class(df=df, variable = "TotalSteps")

#plot_weekday_activity_per_class(database = "fitbit_database.db",
                                #variable = "Calories")
#plot_weekday_activity_per_class(database = "fitbit_database.db",
                               #variable = "TotalDistance")

# === Bullet 4: General insights for dashboard (activity, weekends, weather) ===
conn = sqlite3.connect("fitbit_database.db")

query = '''
SELECT Id, ActivityDate, TotalSteps, Calories, SedentaryMinutes,
       VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes
FROM daily_activity
'''
activity = pd.read_sql_query(query, conn)

activity["ActivityDate"] = pd.to_datetime(activity["ActivityDate"]).dt.normalize()
activity["Id"] = activity["Id"].astype("int64")
activity["TotalActiveMin"] = activity["VeryActiveMinutes"] + activity["FairlyActiveMinutes"] + activity["LightlyActiveMinutes"]

# Daily sleep minutes (count value==1 as asleep)
sleep = pd.read_sql_query("SELECT Id, date, value FROM minute_sleep", conn)
sleep["date"] = pd.to_datetime(sleep["date"])
sleep["day"] = sleep["date"].dt.normalize()
sleep["Id"] = sleep["Id"].astype("int64")

sleep["asleep_min"] = (sleep["value"] == 1).astype(int)
sleep_daily = sleep.groupby(["Id", "day"])["asleep_min"].sum().reset_index()

# Merge activity and sleep
df_daily = activity.merge(sleep_daily, left_on=["Id", "ActivityDate"], right_on=["Id", "day"], how="inner")
df_daily = df_daily.drop(columns=["day"])

# Mark weekends
df_daily["is_weekend"] = df_daily["ActivityDate"].dt.dayofweek >= 5  # Sat=5, Sun=6

conn.close()

print(df_daily[["Id","ActivityDate","TotalSteps","TotalActiveMin","SedentaryMinutes","asleep_min","is_weekend"]].head())

# Daily activity vs sleep duration
plt.figure(figsize=(8,5))
plt.scatter(df_daily["TotalSteps"], df_daily["asleep_min"], alpha=0.4)
plt.xlabel("Total steps per day")
plt.ylabel("Minutes asleep per day")
plt.title("Daily Steps vs Sleep Duration")
plt.tight_layout()
plt.show()

r, p = pearsonr(df_daily["TotalSteps"], df_daily["asleep_min"])
print(f"Correlation (Steps vs Sleep): r={r:.3f}, p={p:.4f}")

r, p = pearsonr(df_daily["TotalActiveMin"], df_daily["asleep_min"])
print(f"Correlation (ActiveMin vs Sleep): r={r:.3f}, p={p:.4f}")

# Weekdays vs weekends
weekdays = df_daily[df_daily["is_weekend"] == False]
weekends  = df_daily[df_daily["is_weekend"] == True]

r_wd, p_wd = pearsonr(weekdays["TotalSteps"], weekdays["asleep_min"])
r_we, p_we = pearsonr(weekends["TotalSteps"], weekends["asleep_min"])

print(f"Weekdays (Steps vs Sleep): r={r_wd:.3f}, p={p_wd:.4f}")
print(f"Weekends (Steps vs Sleep): r={r_we:.3f}, p={p_we:.4f}")

# simple visual comparison of sleep duration
plt.figure(figsize=(6,4))
sns.boxplot(x=df_daily["is_weekend"], y=df_daily["asleep_min"])
plt.xticks([0,1], ["Weekday", "Weekend"])
plt.xlabel("")
plt.ylabel("Minutes asleep")
plt.title("Sleep duration: Weekday vs Weekend")
plt.tight_layout()
plt.show()

# Weather vs activity
weather = pd.read_csv("data/ChicagoWeather.csv")
weather["datetime"] = pd.to_datetime(weather["datetime"]).dt.normalize()
weather = weather[["datetime", "temp", "precip", "windspeed", "feelslike"]]

daily_steps = df_daily.groupby("ActivityDate")["TotalSteps"].mean().reset_index()

# Merge daily steps with weather data by date
daily_weather = daily_steps.merge(weather, left_on="ActivityDate", right_on="datetime", how="left")

daily_weather = daily_weather.dropna(subset=["temp", "TotalSteps"]).copy()

print("Correlation temp vs avg daily steps:", round(daily_weather["temp"].corr(daily_weather["TotalSteps"]), 3))

# Bin temperature into 4 categories and plot average steps per bin
daily_weather["temp_bin"] = pd.cut(daily_weather["temp"], bins=4)
avg_by_bin = daily_weather.groupby("temp_bin")["TotalSteps"].mean()

plt.figure(figsize=(8,4))
plt.bar(avg_by_bin.index.astype(str), avg_by_bin.values)
plt.xticks(rotation=30, ha="right")
plt.title("Average Daily Steps by Temperature Range")
plt.xlabel("Temperature Range (Celsius)")
plt.ylabel("Average Daily Steps")
plt.tight_layout()
plt.show()

# Check correlation and plot for precipitation and windspeed
for col in ["precip", "windspeed"]:
    sub = daily_weather.dropna(subset=[col, "TotalSteps"]).copy()
    print(f"Correlation {col} vs avg daily steps:", round(sub[col].corr(sub["TotalSteps"]), 3))

    sub["bin"] = pd.cut(sub[col], bins=4)
    avg = sub.groupby("bin")["TotalSteps"].mean()

    plt.figure(figsize=(8,4))
    plt.bar(avg.index.astype(str), avg.values)
    plt.xticks(rotation=30, ha="right")
    plt.title(f"Average Daily Steps by {col} range")
    plt.xlabel(f"{col} range (precip in mm, windspeed in km/h)")
    plt.ylabel("Average Daily Steps")
    plt.tight_layout()
    plt.show()