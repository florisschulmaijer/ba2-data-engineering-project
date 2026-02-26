import sqlite3
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates #used to convert time labels to relevant plot labels
import seaborn as sns
import numpy as np

# Connect to database
conn = sqlite3.connect("fitbit_database.db")

# === Bullet 3: Create functions for graphical and statistical summaries for individuals. ===

# === create function to plot daily HR per user ===
# Plot line graph that shows calories burnt each day
def plot_daily_HR(user_id, start_date, end_date=None, database = "fitbit_database.db"):
    #connect to database
    conn = sqlite3.connect(database)

    query = "SELECT * FROM heart_rate"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convert types to correct form
    df["Id"] = df["Id"].astype("Int64")
    df["Time"] = pd.to_datetime(df["Time"], format="%m/%d/%Y %I:%M:%S %p")
    start_date_string = start_date
    end_date_string = end_date
    if end_date is None:
        end_date = start_date #filter on only one date when only one day is given

    #check if user id exists in frame
    if user_id not in df["Id"].values:
        print("ID not found")
        return

    # Filter for user
    user_data = df[df["Id"] == user_id].copy()

    #If date filtering requested
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

def plot_daily_steps(user_id, start_date, end_date=None, database = "fitbit_database.db"):
    #connect to database
    conn = sqlite3.connect(database)

    query = "SELECT * FROM hourly_steps"
    df = pd.read_sql_query(query, conn)
    conn.close()
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
    if start_date == end_date:  # check if only one day is entered, show daily summary
        # Plot data in linegraph for one day
        # Compute max and min HR per day, for plotting later
        # Get row with max hourly steps
        max_row = user_data.loc[user_data["StepTotal"].idxmax()]
        # Get row with min hourly steps
        min_row = user_data.loc[user_data["StepTotal"].idxmin()]

        # Create a summary DataFrame
        st_summary = pd.DataFrame({
            "Type": ["Max", "Min"],
            "StepTotal": [max_row["StepTotal"], min_row["StepTotal"]],
            "Time": [max_row["Time"], min_row["Time"]],
            "Hour": [max_row["Time"].hour, min_row["Time"].hour]
        })

        # Resample / group by hourly intervals
        user_data = user_data.set_index("Time")
        st_agg = user_data["StepTotal"].resample("h").mean()

        plt.figure(figsize=(12, 6))
        plt.bar(st_agg.index, st_agg.values, width=0.03, color='skyblue', edgecolor='black')
        # Format x-axis to show hours only
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator())
        plt.xlabel("Hour")
        plt.ylabel("Steps per Hour")
        plt.title(f"Steps per Hour for User {user_id} on {start_date_string}")

        # Add min and max values
        for _, row in st_summary.iterrows():

            if row["Type"] == "Max":
                offset = 10
                va = "bottom"
            else:  # Min
                offset = -15
                va = "top"

            plt.annotate(
                f"{row['Type']}: {row['StepTotal']}",
                xy=(row["Time"], row["StepTotal"]),
                xytext=(0, offset),
                textcoords='offset points',
                ha='center',
                va=va,
                arrowprops=dict(arrowstyle="->", color='red')
            )

        plt.show()
        plt.show()

    # Plot data in linegraph
    else:
        # Compute max and min HR per day, for plotting later
        # Get row with max hourly steps
        max_row = user_data.loc[user_data["StepTotal"].idxmax()]
        # Get row with min hourly steps
        min_row = user_data.loc[user_data["StepTotal"].idxmin()]

        # Create a summary DataFrame
        st_summary = pd.DataFrame({
            "Type": ["Max", "Min"],
            "StepTotal": [max_row["StepTotal"], min_row["StepTotal"]],
            "Time": [max_row["Time"], min_row["Time"]],
            "Hour": [max_row["Time"].hour, min_row["Time"].hour]
        })

        # Resample / group by 4 hour intervals
        user_data = user_data.set_index("Time")
        st_agg = user_data["StepTotal"].resample("4h").sum()

        plt.figure(figsize=(12, 6))
        plt.bar(st_agg.index, st_agg.values, width=0.03, color='skyblue', edgecolor='black')

        plt.xlabel("Date")
        plt.ylabel("Steps per 4 Hours")
        plt.title(f"Steps per 4 Hours for User {user_id} between {start_date_string} and {end_date_string}")
        # Add min and max values
        # Add min and max values
        for _, row in st_summary.iterrows():

            if row["Type"] == "Max":
                offset = 10
                va = "bottom"
            else:  # Min
                offset = -15
                va = "top"

            plt.annotate(
                f"{row['Type']}: {row['StepTotal']}",
                xy=(row["Time"], row["StepTotal"]),
                xytext=(0, offset),
                textcoords='offset points',
                ha='center',
                va=va,
            )
        plt.show()


plot_daily_steps(2022484408, start_date="2016-04-02")
plot_daily_steps(2022484408, start_date="2016-04-02", end_date="2016-04-06")

#=== define function for plotting HR, sleep duration and sleep value per user
def individual_sleep(date, userid, database = ):





#=== Complete Datasetlevel summaries ===
#plot distribution of steps per weekday for each user class (heavy, light, moderate)
def plot_weekday_activity_per_class(database = "fitbit_database.db",
                                    variable="TotalDistance"):
    # connect to database
    conn = sqlite3.connect(database)

    query = "SELECT * FROM daily_activity"
    df = pd.read_sql_query(query, conn)
    conn.close()

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
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x="DayOfWeek", y= variable, hue="Class",
                order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                hue_order=["Light", "Moderate", "Heavy"])
    plt.xlabel("Day of the week")
    plt.ylabel(variable)
    plt.title(f'Distribution of {variable} per weekday and user class')

    plt.show()

#Generate some plots
plot_weekday_activity_per_class(database = "fitbit_database.db",
                                variable = "TotalSteps")

plot_weekday_activity_per_class(database = "fitbit_database.db",
                                variable = "Calories")
plot_weekday_activity_per_class(database = "fitbit_database.db",
                                variable = "TotalDistance")

