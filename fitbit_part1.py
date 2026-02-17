import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import statsmodels.formula.api as smf # Used when providing formula to regression model
import statsmodels.api as sm # Used when manually provide X and y to regression model

# === Basic Inspection of the data ===

# Load data
df = pd.read_csv("data/daily_activity.csv")

# Count unique users
num_unique_users = df["Id"].nunique()
print(f"Number of unique users: {num_unique_users}")

# Compute total distance for each user
total_distance = df.groupby("Id")["TotalDistance"].sum().sort_values()
print(f"Total distance for each user:\n{total_distance}")

# Plot bar chart of total distance for each user
plt.figure(figsize=(12, 6))
total_distance.plot(kind="bar")
plt.title("Total Distance per User")
plt.xlabel("User ID")
plt.ylabel("Total Distance")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

# Convert "ActivityDate" to datetime 
df["ActivityDate"] = pd.to_datetime(df["ActivityDate"])

# Plot line graph that shows calories burnt each day
def plot_calories_burnt(user_id, start_date=None, end_date=None):

    # Filter data for user ID
    user_data = df[df["Id"] == user_id].copy()

    # Filter data for date range if provided
    if start_date is not None and end_date is not None:
        start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")
        user_data = user_data[(user_data["ActivityDate"] >= start_date) & (user_data["ActivityDate"] <= end_date)]

    user_data = user_data.sort_values("ActivityDate")

    plt.figure(figsize=(12, 6))
    plt.plot(user_data["ActivityDate"], user_data["Calories"], marker="o")
    plt.title(f"Calories Burnt per Day (User {user_id})")
    plt.xlabel("Date")
    plt.ylabel("Calories Burnt")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

plot_calories_burnt(1503960366)
plot_calories_burnt(1503960366, "2016-03-20", "2016-03-30")

# Get day of the week for each activity date
df["DayOfWeek"] = df["ActivityDate"].dt.day_name()

# Count how many times each day of the week appears in the data (frequency of workouts on each day)
workout_frequency = df["DayOfWeek"].value_counts()

# Reorder the days of the week
days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

workout_frequency = workout_frequency.reindex(days_order)

print("Checking the workout frequency data:")
print(workout_frequency)
print(workout_frequency.index)
print(workout_frequency.values)

# Plot bar chart
plt.figure(figsize=(10, 5))
plt.bar(workout_frequency.index, workout_frequency.values)
plt.title("Frequency of Workouts by Day of the Week")
plt.xlabel("Day of the Week")
plt.ylabel("Number of Workouts")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# === Relationship between calories and steps taken ===

# Linear regression model
model = smf.ols(formula="Calories ~ TotalSteps + C(Id)", data=df).fit()
print(model.summary())

def plot_user_regression(user_id):

    # Filter data for selected user
    user_data = df[df["Id"] == user_id].copy()
    
    # Define variables
    X = user_data["TotalSteps"]
    y = user_data["Calories"]
    
    # Add constant (intercept)
    X = sm.add_constant(X)
    
    # Fit regression for this user only
    model = sm.OLS(y, X).fit()
    
    # Create predicted values
    user_data["Predicted"] = model.predict(X)
    
    user_data = user_data.sort_values("TotalSteps")

    # Plot scatter
    plt.figure(figsize=(8,6))
    plt.scatter(user_data["TotalSteps"], user_data["Calories"], alpha=0.7)
    
    # Plot regression line
    plt.plot(user_data["TotalSteps"], user_data["Predicted"], color="red")
    
    plt.title(f"Steps vs Calories for User {user_id}")
    plt.xlabel("Total Steps")
    plt.ylabel("Calories")
    plt.tight_layout()
    plt.show()
    
    # Print regression summary for this user
    print(model.summary())

plot_user_regression(1503960366)