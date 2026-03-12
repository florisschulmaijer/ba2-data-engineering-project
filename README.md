# FitBit Analytics Dashboard 2016

An interactive data dashboard built with Python and Streamlit that analyses fitness data from 35 Fitbit users collected during a 2016 Amazon survey. The dashboard is aimed at business analysts working for a fitness tracker manufacturer, as well as the study participants themselves.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Requirements](#requirements)
4. [How to Run the Dashboard](#how-to-run-the-dashboard)
5. [Dashboard Pages](#dashboard-pages)
6. [Data Sources](#data-sources)
7. [Analysis Scripts](#analysis-scripts)
8. [Team & Collaboration](#team--collaboration)

---

## Project Overview

This project was built as part of the BA2 Data Engineering course at Vrije Universiteit Amsterdam. It progresses through six parts:

- **Part 1** — Exploratory data analysis on daily activity data
- **Part 2** — GitHub repository setup and version control
- **Part 3** — SQLite database interaction and user classification
- **Part 4** — Data wrangling: merging tables, weight imputation, group-level summaries
- **Part 5** — Interactive Streamlit dashboard
- **Part 6** — Deployment via Streamlit Community Cloud

Users are classified into three groups based on how many days they recorded activity:

| Class    | Days recorded |
|----------|--------------|
| Light    | ≤ 10 days    |
| Moderate | 11–15 days   |
| Heavy    | ≥ 16 days    |

---

## Repository Structure

```
BA2_DataEngineering_Project/
├── .git/                          ← Git version control (do not modify)
├── data/
│   ├── daily_activity.csv         ← Raw daily activity data
│   └── ChicagoWeather.csv         ← Chicago weather data for the study period
├── pages/
│   ├── Weekday vs Weekend Analysis.py       ← Dashboard page
│   ├── Individual Step Statistics.py        ← Dashboard page
│   └── Individual Heart Rate & Intensity.py ← Dashboard page
├── scripts/
│   ├── fitbit_part1.py            ← Part 1 standalone analysis (EDA, regression)
│   └── database_part3.py          ← Part 3 standalone analysis (sleep, 4-hour blocks)
├── .gitignore                     ← Files excluded from version control
├── datawrangling_part4.py         ← Part 4 analysis + reusable plot functions (imported by dashboard)
├── fitbit_database.db             ← SQLite database with all study tables
├── Home.py                        ← Main Streamlit entry point
└── README.md                      ← This file
```

---

## Requirements

Make sure you have Python 3.9 or later installed. Install all required packages with:

```bash
pip install streamlit pandas matplotlib seaborn scipy statsmodels
```

Or, using a virtual environment:

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
pip install streamlit pandas matplotlib seaborn scipy statsmodels
```

---

## How to Run the Dashboard

1. **Clone the repository**

```bash
git clone <repository-url>
cd BA2_DataEngineering_Project
```

2. **Install dependencies** (see [Requirements](#requirements) above)

3. **Start the dashboard**

```bash
streamlit run Home.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`.

> **Note:** The `fitbit_database.db` file must be present in the project root. It is included in the repository.

---

## Dashboard Pages

### Home — Group Summary

The landing page displays group-level statistics across all 35 participants:

- Key metrics: total users, study period, average steps, calories, and sedentary minutes
- Numerical summary table broken down by user class (Light / Moderate / Heavy)
- Bar charts comparing average daily steps and calories per user class
- Interactive boxplot showing the distribution of any chosen activity metric across weekdays, split by user class

### Weekday vs Weekend Analysis

Compares activity and sleep patterns between weekdays (Monday–Friday) and weekends (Saturday–Sunday):

- Summary metric cards showing weekend vs weekday deltas for steps, calories, active minutes, sedentary minutes, and sleep duration
- Side-by-side bar charts for steps, calories, and sleep
- Day-of-week bar chart with weekends highlighted in a distinct colour
- User-class breakdown: how weekday vs weekend differences vary for Light, Moderate, and Heavy users
- Optional individual user filter in the sidebar

### Individual Step Statistics

Explores the step patterns of a single user:

- Hourly step chart for a selected date or date range
- Activity summary (total steps, avg steps, avg calories, avg active minutes) for the selected period
- Group comparison section showing how the selected user's average steps compare to the group

**How to use:**
1. Select a User ID in the sidebar
2. Choose a start and end date from the dropdown (only dates with recorded data are shown)
3. The chart and summary update automatically

### Individual Heart Rate & Intensity

Plots hourly average heart rate and total exercise intensity on a dual-axis chart:

- Heart rate (bpm) on the left y-axis in red
- Total intensity on the right y-axis in blue
- Date range filter in the sidebar

Heart-rate data is available for 14 of the 35 users. A start date from 1 April 2016 is recommended as March data may be incomplete.

**How to use:**
1. Select a User ID from the available list in the sidebar
2. Set a start and end date
3. The dual-axis chart updates automatically

---

## Data Sources

The project uses the `fitbit_database.db` SQLite database, which contains the following tables:

| Table              | Description                                                                      |
|--------------------|----------------------------------------------------------------------------------|
| `daily_activity`   | Daily totals per user: steps, distance, calories, active and sedentary minutes   |
| `heart_rate`       | Heart rate sampled every 5 seconds                                               |
| `hourly_calories`  | Calories burned per hour                                                         |
| `hourly_intensity` | Exercise intensity (total and average) per hour                                  |
| `hourly_steps`     | Steps taken per hour                                                             |
| `minute_sleep`     | Minute-by-minute sleep state (1 = asleep, 2 = restless, 3 = awake)              |
| `weight_log`       | Weight, fat percentage, and BMI logs                                             |

Additionally, `data/ChicagoWeather.csv` contains weather data (temperature, precipitation, windspeed) for Chicago during the study period, used to investigate weather–activity relationships.

---

## Analysis Scripts

The standalone analysis scripts live in `scripts/` and can be run directly. `datawrangling_part4.py` sits at the root because it is imported by the dashboard pages.

| Script                     | Location   | Contents                                                                                    |
|----------------------------|------------|---------------------------------------------------------------------------------------------|
| `fitbit_part1.py`          | `scripts/` | EDA: unique users, total distance per user, calories over time, workout frequency, OLS regression |
| `database_part3.py`        | `scripts/` | Sleep duration analysis, sedentary vs sleep regression, 4-hour activity block analysis, HR+intensity function |
| `datawrangling_part4.py`   | root       | Weight imputation, table merging, individual plot functions used by the dashboard, weekday/weekend and weather analysis |

To run the standalone scripts from the project root:

```bash
python scripts/fitbit_part1.py
python scripts/database_part3.py
```

---

## Team & Collaboration

This project was developed by a team of 3 students using GitHub for version control. Each new feature was developed on a separate branch and merged into `main` via pull requests.

**Workflow:**
1. Create a new branch: `git checkout -b <branch-name>`
2. Make changes and commit: `git commit -m "descriptive message"`
3. Push the branch: `git push origin <branch-name>`
4. Open a pull request on GitHub and request a review
5. After approval, merge into `main`

All team members contributed to both the analysis scripts and the dashboard code. The commit history reflects individual contributions per team member.
