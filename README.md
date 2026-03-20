# FitBit Analytics Dashboard 2016

An interactive data dashboard built with Python and Streamlit that analyses fitness data from 35 Fitbit users collected during a 2016 Amazon survey. The dashboard is aimed at business analysts working for a fitness tracker manufacturer, as well as the study participants themselves.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure & Flow](#repository-structure--flow)
3. [Requirements](#requirements)
4. [How to Run the Dashboard](#how-to-run-the-dashboard)
5. [Dashboard Pages](#dashboard-pages)
6. [Data Sources](#data-sources)
7. [Analysis Scripts](#analysis-scripts)
8. [Team & Collaboration](#team--collaboration)

---

## Project Overview

This project was built as part of the BA2 Data Engineering course at Vrije Universiteit Amsterdam. It progresses through six parts:

- **Part 1** — Exploratory data analysis on daily activity data (`scripts/fitbit_part1.py`)
- **Part 2** — GitHub repository setup and version control
- **Part 3** — SQLite database creation and interaction (`scripts/database_part3.py`)
- **Part 4** — Data wrangling: table merging, weight imputation, reusable plot functions (`datawrangling_part4.py`)
- **Part 5** — Interactive Streamlit dashboard (`Home.py` + `pages/`)
- **Part 6** — Deployment via Streamlit Community Cloud

Users are classified into three groups based on how many days they recorded activity:

| Class    | Days recorded |
|----------|--------------|
| Light    | ≤ 10 days    |
| Moderate | 11–15 days   |
| Heavy    | ≥ 16 days    |

---

## Repository Structure & Flow

```
BA2_DataEngineering_Project/
│
│   ── PIPELINE ──────────────────────────────────────────────────────────
│
├── data/
│   ├── daily_activity.csv          ← Raw CSV exported from the Fitbit dataset
│   └── ChicagoWeather.csv          ← Chicago weather data for the study period
│
├── scripts/
│   ├── fitbit_part1.py             ← Part 1: EDA on raw CSV (runs standalone)
│   ├── database_part3.py           ← Part 3: builds & queries the SQLite database
│   └── sleep_regression.py         ← OLS regression: activity → sleep duration
│
├── fitbit_database.db              ← SQLite database (output of database_part3.py)
│
│   ── DASHBOARD ──────────────────────────────────────────────────────────
│
├── datawrangling_part4.py          ← Part 4: data wrangling + reusable plot
│                                      functions imported by all dashboard pages
│
├── Home.py                         ← Streamlit entry point (group overview)
│
├── pages/
│   ├── Heart Rate & Intensity.py   ← Per-user HR vs intensity dual-axis chart
│   ├── Sleep Statistics.py         ← Per-user sleep stages and nightly duration
│   ├── Step Statistics.py          ← Per-user hourly step patterns
│   ├── Weather Analysis.py         ← Weather vs activity correlation explorer
│   └── Weekday vs Weekend.py       ← Weekday vs weekend activity & sleep comparison
│
│   ── CONFIG ────────────────────────────────────────────────────────────
│
├── requirements.txt                ← Python dependencies for deployment
└── README.md                       ← This file
```

---

## Requirements

Install all dependencies from the requirements file:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install streamlit pandas numpy matplotlib seaborn scipy statsmodels
```

Python 3.9 or later is required.


## How to Run the Dashboard

1. **Clone the repository**

```bash
git clone <repository-url>
cd BA2_DataEngineering_Project
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Ensure the database exists**

The `fitbit_database.db` file is included in the repository. If it is missing, regenerate it by running:

```bash
python scripts/database_part3.py
```

4. **Start the dashboard**

```bash
streamlit run Home.py
```

The dashboard opens automatically at `http://localhost:8501`.

---

## Dashboard Pages

### Home
Group-level statistics across all 35 participants:
- KPI cards: total users, study period, average daily steps, calories, and sedentary minutes
- Summary table broken down by user class (Light / Moderate / Heavy)
- Bar charts comparing average steps and calories per user class
- Interactive boxplot of any activity metric across weekdays, split by user class

### Heart Rate & Intensity
Dual-axis chart of hourly average heart rate and exercise intensity for a single user:
- Heart rate (bpm) on the left axis
- Total intensity on the right axis
- Date range filter in the sidebar
- Available for 14 of the 35 users (those with HR data)

### Sleep Statistics
Per-user sleep exploration across selected nights:
- Minute-level sleep stage bar chart (Asleep / Restless / Awake)
- Horizontal summary bar showing the proportion of each stage
- Weekly overview of average sleep duration, split by naps vs full nights

### Step Statistics
Per-user step patterns for a selected date range:
- Hourly step chart (single day) or 4-hour aggregated chart (multi-day)
- Period summary: total steps, avg steps, avg calories, avg active minutes
- Group comparison showing the user's rank relative to all 35 participants

### Weather Analysis
Scatter plot with regression line exploring the relationship between a chosen weather variable and a chosen activity variable (group averages per day):
- Weather variables: temperature, feels like, precipitation, windspeed, humidity
- Activity variables: steps, distance, active minutes, sedentary minutes, calories
- Pearson r and p-value displayed below the chart

### Weekday vs Weekend
Comparison of activity and sleep between weekdays and weekends:
- Metric cards showing weekend vs weekday deltas for steps, calories, active minutes, sedentary minutes, and sleep
- Side-by-side bar charts and a day-of-week breakdown
- Optional individual user filter in the sidebar

---

## Data Sources

### SQLite Database — `fitbit_database.db`

| Table              | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `daily_activity`   | Daily totals per user: steps, distance, calories, active and sedentary minutes |
| `heart_rate`       | Heart rate sampled every 5 seconds                                          |
| `hourly_calories`  | Calories burned per hour                                                    |
| `hourly_intensity` | Exercise intensity (total and average) per hour                             |
| `hourly_steps`     | Steps taken per hour                                                        |
| `minute_sleep`     | Minute-by-minute sleep state (1 = asleep, 2 = restless, 3 = awake)         |
| `weight_log`       | Weight, fat percentage, and BMI logs                                        |

### CSV Files — `data/`

| File                  | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| `daily_activity.csv`  | Raw daily activity data used in Part 1 EDA                         |
| `ChicagoWeather.csv`  | Weather data (temp, precipitation, windspeed) for the study period |

---

## Analysis Scripts

Standalone scripts in `scripts/` can be run directly from the project root. They do not require the dashboard to be running.

| Script                   | Contents                                                                                         |
|--------------------------|--------------------------------------------------------------------------------------------------|
| `fitbit_part1.py`        | EDA on raw CSV: unique users, total distance per user, calories over time, OLS regression        |
| `database_part3.py`      | Creates the SQLite database, sleep duration analysis, sedentary vs sleep regression, HR+intensity |
| `sleep_regression.py`    | OLS regression of total active minutes and sedentary minutes on sleep duration, QQ plot, Shapiro-Wilk normality test |

```bash
python scripts/fitbit_part1.py
python scripts/database_part3.py
python scripts/sleep_regression.py
```

`datawrangling_part4.py` lives at the root (not in `scripts/`) because it is imported directly by the dashboard pages.

---

## Team & Collaboration

This project was developed by a team of 4 students using GitHub for version control. Each feature was developed on a separate branch and merged into `main` via pull request.

**Workflow:**
1. Create a branch: `git checkout -b <branch-name>`
2. Commit changes: `git commit -m "descriptive message"`
3. Push: `git push origin <branch-name>`
4. Open a pull request and request a review
5. Merge into `main` after approval
