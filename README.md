# BA2 Data Engineering Project  
## Fitbit Activity Analysis
---
## Project Overview
This project analyses Fitbit activity data using Python and SQL.  
The focus is on exploring relationships between physical activity, calories burned, and sleep behavior.

---
# Part 1 – Exploratory Data Analysis
We worked with `daily_activity.csv`.
### Basic Inspection
- Counted number of unique users  
- Computed total distance per user  
- Visualized total distance in a bar chart  
### Calories Over Time
Created a function:
```python
plot_calories_burnt(user_id, start_date=None, end_date=None)
```
This:
- Filters data for a specific user  
- Optionally filters by date range  
- Plots calories burned per day  
### Workout Frequency
- Extracted weekday from date  
- Counted workout frequency per weekday  
- Visualized results in a bar chart  
### Linear Regression
Estimated:
Calories = β₀ + β₁ · TotalSteps + β₂ · Id + ε  
Using:
```python
smf.ols("Calories ~ TotalSteps + C(Id)", data=df)
```
Additionally:
- Built a function to visualize scatterplot + regression line per user
- Built a function to visualize linegraph of total daily steps per user
- Built  functions to visualize total daily active distance and active minutes per user in stacked bar graphs
---

# Part 2 – GitHub Setup
- Created a private GitHub repository  
- Added Python files and README  
- Used branches and pull requests for collaboration  
---

# Part 3 – Database Interaction
Connected to `fitbit_database.db` using `sqlite3`.
## User Classification
Used SQL:
```sql
SELECT Id, COUNT(*) as days
FROM daily_activity
GROUP BY Id;
```
Users classified as:
- Light (≤10 days)
- Moderate (11–15 days)
- Heavy (≥16 days)
Classification applied in Python and stored in a DataFrame.

## Sedentary Minutes vs Sleep Duration
For this part we check if days with more sitting time are linked to more or less sleep.
First, we pull the columns we need (Id, ActivityDate, SedentaryMinutes) from the daily_activity table. 
Then we make sure the date column is in the same "day format" as the sleep data (so the dates line up when we combine the two datasets). After that, we join the sedentary data with our daily sleep table (df_daily_sleep) so each row represents the same user on the same day with both values available.
Finally, we run a simple linear regression: 

Duration ~ SedentaryMinutes + C(Id)

This gives us an estimate of how sleep duration changes when sedentary minutes change, while C(Id) helps account for the fact that different people naturally sleep different amounts.

What you should see when running the script:
- A regression summary printed in the console.
- Two plots to check the regression quality:
  - A histogram of residuals.
  - A Q–Q plot of residuals.

## 4-Hour Block Analysis 
In this part we wanted to see when during the day people are most active and when they sleep. To do that, we split every day into 6 simple time blocks: 0–4, 4–8, 8–12, 12–16, 16–20, 20–24.
We made a small helper function (hour_to_time_block) that takes an hour and returns which 4-hour block it belongs to. Then we used the same idea for steps, calories, and sleep:
### Steps
- Load the hourly_steps table.
- Convert ActivityHour to datetime.
- Assign each row to a 4-hour block.
- Take the average StepTotal per block.
- Plot a bar chart: _Average steps per 4-hour block._
### Calories
- Load the hourly_calories table.
- Convert ActivityHour to datetime.
- Assign each row to a 4-hour block.
- Take the average Calories per block.
- Plot a bar chart: _Average calories per 4-hour block._
### Sleep minutes
- Load the minute_sleep table (this is minute-by-minute sleep data).
- Convert date to datetime and assign each minute to a 4-hour block.
- Keep only rows where value == 1 (minutes marked as "asleep").
- Count asleep minutes per person + day + block, then average those values.
- Plot a bar chart: _Average minutes asleep per 4-hour block._

What you should see when running the script:
- 3 bar charts:
  - Average steps per 4-hour block.
  - Average calories per 4-hour block.
  - Average minutes asleep per 4-hour block.

### How heart rate relates to exercise intensity for a given user
- Loaded data and hourly intensity data from databases
- Cleaned, and aligned by User ID and Hour
- Heart Rate is aggregated to hourly average and merged with total intensity

- The function plot_user_HR_exercise_int(id) produces a dual-axis plot showing how a user's average heart rate varies alongside their exercise intensity over time
- Key output: Hourly heart-rate vs. intensity visualization for any user ID

### Weather and Activity Correlations
- Daily activities metrics are merged with Chicago weather data 
- Activity is aggregated by date and by activity class
- Pearson correlations are computed between these two variab;es
- Only statistically significant pairs are visualized
- A class-wise LOWESS analysis indicates how different activity groups respond to weather conditions.

- Key output: Correlation table, multi-panel regression plots
---

# Technologies Used
- Python (pandas, matplotlib, statsmodels)
- SQLite (sqlite3)
- Git & GitHub
