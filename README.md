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

### User Classification

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

---

# Technologies Used

- Python (pandas, matplotlib, statsmodels)
- SQLite (sqlite3)
- Git & GitHub
