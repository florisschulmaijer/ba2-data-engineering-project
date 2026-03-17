import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import sqlite3

# === Page config ===
st.set_page_config(
    page_title="Weekday vs Weekend",
    page_icon="fitbit",
    layout="wide",
    initial_sidebar_state="expanded"
)

BG_COLOR = "#111420"
C_BLUE = "#4C9BE8"
C_ORANGE = "#E8834C"
C_GREEN = "#52C97A"
C_GRAY = "#9B9EAC"
C_PURPLE = "#A78BFA"

def style_ax(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

# Sidebar
st.sidebar.markdown(
    """
    <div style="padding: 12px 4px 8px 4px;">
        <div style="color:white; font-size:1.1rem; font-weight:700; margin-bottom:4px;">Weekday vs Weekend</div>
        <div style="color:#9B9EAC; font-size:0.78rem; line-height:1.5;">
            Activity and sleep patterns compared across weekdays and weekends.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()

# === Data loading ===
@st.cache_data
def load_activity(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM daily_activity", conn)
    conn.close()
    return df

@st.cache_data
def load_sleep(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT Id, date, value FROM minute_sleep", conn)
    conn.close()
    return df

df_activity  = load_activity()
df_sleep_raw = load_sleep()

# Process activity data
df = df_activity.copy()
df["ActivityDate"] = pd.to_datetime(df["ActivityDate"], format="%m/%d/%Y")
df["Id"] = df["Id"].astype("Int64")
df["DayOfWeek"] = df["ActivityDate"].dt.day_name()
df["IsWeekend"] = df["ActivityDate"].dt.dayofweek >= 5
df["DayType"] = df["IsWeekend"].map({True: "Weekend", False: "Weekday"})
df["Class"] = df.groupby("Id")["Id"].transform("count").apply(
    lambda days: "Light" if days <= 10 else ("Moderate" if days <= 15 else "Heavy")
)

# Process sleep data
df_sleep_raw["date"] = pd.to_datetime(df_sleep_raw["date"])
df_sleep_raw["day"] = df_sleep_raw["date"].dt.normalize()
df_sleep_raw["Id"] = df_sleep_raw["Id"].astype("Int64")
df_sleep_raw["asleep"] = (df_sleep_raw["value"] == 1).astype(int)
df_sleep_daily = (
    df_sleep_raw.groupby(["Id", "day"])["asleep"]
    .sum().reset_index()
    .rename(columns={"day": "ActivityDate", "asleep": "asleep_min"})
)

# Merge
df_merged = df.merge(df_sleep_daily, on=["Id", "ActivityDate"], how="left")

# === Sidebar user filter — defined BEFORE plots so selection affects all charts ===
st.sidebar.markdown("**Filter by user (optional)**")
all_ids = sorted(df_merged["Id"].dropna().unique().tolist())
selected_id = st.sidebar.selectbox(
    "User ID",
    [None] + all_ids,
    format_func=lambda x: "All users" if x is None else str(x)
)

# Apply filter — plot_df is used by all charts below
plot_df = df_merged[df_merged["Id"] == selected_id] if selected_id is not None else df_merged
weekday_df = plot_df[plot_df["DayType"] == "Weekday"]
weekend_df = plot_df[plot_df["DayType"] == "Weekend"]

# Page header
label = f"User {selected_id}" if selected_id is not None else "All users"
st.title("Weekday vs Weekend")
st.caption(f"How do activity and sleep differ between working days and the weekend? — {label}")
st.divider()

# Metric cards
with st.container(border=True):
    st.markdown("**Weekend averages vs weekday baseline**")
    metrics_config = {
        "TotalSteps": ("Avg Steps", C_BLUE),
        "Calories": ("Avg Calories", C_ORANGE),
        "VeryActiveMinutes": ("Very Active Min", C_GREEN),
        "SedentaryMinutes": ("Sedentary Min", C_GRAY),
        "asleep_min": ("Sleep (min)", C_PURPLE),
    }
    cols = st.columns(5)
    for col, (metric, (lbl, color)) in zip(cols, metrics_config.items()):
        wd_val = weekday_df[metric].mean()
        we_val = weekend_df[metric].mean()
        delta_pct = ((we_val - wd_val) / wd_val * 100) if wd_val and wd_val != 0 else 0
        col.metric(lbl, f"{we_val:,.0f}", f"{delta_pct:+.1f}%")

st.write("")

# Bar charts
with st.container(border=True):
    st.markdown("**Side-by-side comparison**")
    colors_dt = {"Weekday": C_BLUE, "Weekend": C_ORANGE}
    plot_metrics = [
        ("TotalSteps", "Avg Daily Steps"),
        ("Calories", "Avg Daily Calories"),
        ("asleep_min", "Avg Sleep (min)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.patch.set_facecolor(BG_COLOR)
    for ax, (metric, title) in zip(axes, plot_metrics):
        style_ax(ax)
        avg_by_type = plot_df.groupby("DayType")[metric].mean().reindex(["Weekday", "Weekend"])
        bars = ax.bar(avg_by_type.index, avg_by_type.values,
                      color=[colors_dt[t] for t in avg_by_type.index], width=0.5)
        ax.set_title(title)
        ax.set_xlabel("")
        max_val = avg_by_type.max()
        for bar, val in zip(bars, avg_by_type.values):
            if not np.isnan(val):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max_val * 0.01,
                        f"{val:,.0f}", ha="center", fontsize=11, color="white", fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig)

# Day-of-week breakdown
with st.container(border=True):
    metric_choice = st.selectbox(
        "Metric",
        ["TotalSteps", "Calories", "VeryActiveMinutes", "SedentaryMinutes"],
        key="day_metric"
    )
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekend_days = {"Saturday", "Sunday"}
    daily_avg = plot_df.groupby("DayOfWeek")[metric_choice].mean().reindex(day_order)

    fig2, ax2 = plt.subplots(figsize=(12, 4))
    fig2.patch.set_facecolor(BG_COLOR)
    style_ax(ax2)
    bars2 = ax2.bar(day_order, daily_avg.values,
                    color=[C_ORANGE if d in weekend_days else C_BLUE for d in day_order])
    ax2.set_title(f"Avg {metric_choice} by Day of Week", color="white", fontsize=13)
    plt.xticks(rotation=15)
    for bar, val in zip(bars2, daily_avg.values):
        if not np.isnan(val):
            ax2.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + daily_avg.max() * 0.005,
                     f"{val:,.0f}", ha="center", fontsize=9, color="white")
    ax2.legend(
        handles = [mpatches.Patch(facecolor=C_BLUE, label="Weekday"),
                 mpatches.Patch(facecolor=C_ORANGE, label="Weekend")],
        facecolor = "#1e2130", labelcolor="white"
    )
    plt.tight_layout()
    st.pyplot(fig2)
