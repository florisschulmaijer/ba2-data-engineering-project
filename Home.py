import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3
from datawrangling_part4 import plot_weekday_activity_per_class

# === Page config ===
st.set_page_config(
    page_title="FitBit Analytics 2016",
    page_icon="fitbit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Shared colour palette
BG_COLOR     = "#111420"
C_BLUE       = "#4C9BE8"
C_ORANGE     = "#E8834C"
C_GREEN      = "#52C97A"
CHART_COLORS = [C_BLUE, C_ORANGE, C_GREEN]

def style_ax(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

def kpi_card(label, value, color=C_BLUE):
    st.markdown(
        f"""
        <div style="
            background-color: #191d2e;
            border-top: 3px solid {color};
            border-radius: 8px;
            padding: 16px 20px 14px 20px;
        ">
            <div style="color: #9B9EAC; font-size: 0.75rem; text-transform: uppercase;
                        letter-spacing: 0.07em; margin-bottom: 6px;">{label}</div>
            <div style="color: #ffffff; font-size: 1.6rem; font-weight: 700;
                        line-height: 1.1;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Sidebar
st.sidebar.title("FitBit Analytics 2016")
st.sidebar.markdown("**Home**")
st.sidebar.caption("Group-level overview of all 35 participants.")
st.sidebar.divider()
st.sidebar.markdown(
    "- **Home** — overview\n"
    "- **Weekday vs Weekend** — activity patterns\n"
    "- **Individual Step Statistics** — per-user steps\n"
    "- **Individual Heart Rate & Intensity** — HR over time"
)

# === Data loading ===
@st.cache_data
def load_activity_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM daily_activity", conn)
    conn.close()
    return df

@st.cache_data
def load_heart_rate_data(database="fitbit_database.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql_query("SELECT * FROM heart_rate", conn)
    conn.close()
    return df

df_activity   = load_activity_data()
df_heart_rate = load_heart_rate_data()

# Prepare overview frame
df_overview = df_activity.copy()
df_overview["ActivityDate"] = pd.to_datetime(df_overview["ActivityDate"], format="%m/%d/%Y")
df_overview["Id"]           = df_overview["Id"].astype("Int64")
df_overview["Class"]        = df_overview.groupby("Id")["Id"].transform("count").apply(
    lambda days: "Light" if days <= 10 else ("Moderate" if days <= 15 else "Heavy")
)

# Page header
st.title("FitBit Analytics — 2016 Study")
st.caption("35 participants · April–May 2016 · Chicago")
st.markdown(
    "This dashboard explores fitness tracker data collected from 35 Fitbit users during a 2016 Amazon survey. "
    "Use the **Overview** tab for group-wide statistics, the **Leaderboard** to rank users by activity, "
    "or the sidebar pages to dig into individual step patterns and heart rate data."
)
st.divider()

# === Tabs ===
tab_overview, tab_leaderboard, tab_weekday = st.tabs([
    "Overview",
    "Leaderboard",
    "Weekday Patterns",
])

# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab_overview:

    # KPI cards
    n_users       = df_overview["Id"].nunique()
    date_min      = df_overview["ActivityDate"].min()
    date_max      = df_overview["ActivityDate"].max()
    avg_steps     = int(df_overview["TotalSteps"].mean())
    avg_calories  = int(df_overview["Calories"].mean())
    avg_sedentary = int(df_overview["SedentaryMinutes"].mean())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi_card("Participants",       str(n_users),                    C_BLUE)
    with c2: kpi_card("Study Start",        date_min.strftime("%d/%m/%Y"),   C_BLUE)
    with c3: kpi_card("Study End",          date_max.strftime("%d/%m/%Y"),   C_BLUE)
    with c4: kpi_card("Avg Daily Steps",    f"{avg_steps:,}",                C_ORANGE)
    with c5: kpi_card("Avg Daily Calories", f"{avg_calories:,}",             C_GREEN)
    with c6: kpi_card("Avg Sedentary Min",  f"{avg_sedentary:,}",            "#9B9EAC")

    st.write("")

    # Summary table
    with st.container(border=True):
        st.markdown("**Summary by User Class**")
        with st.expander("What are user classes?"):
            st.caption(
                "Light — up to 10 days recorded  |  "
                "Moderate — 11–15 days  |  "
                "Heavy — 16+ days"
            )
        summary_table = (
            df_overview.groupby("Class")[["TotalSteps", "Calories", "VeryActiveMinutes", "SedentaryMinutes"]]
            .agg(["mean", "median", "std"])
            .round(1)
            .reindex(["Light", "Moderate", "Heavy"])
        )
        summary_table.columns = [" ".join(col) for col in summary_table.columns]
        st.dataframe(summary_table, use_container_width=True)

    # Bar charts
    with st.container(border=True):
        st.markdown("**Avg Steps & Calories by User Class**")
        class_order = ["Light", "Moderate", "Heavy"]
        class_avg   = df_overview.groupby("Class")[["TotalSteps", "Calories"]].mean().reindex(class_order)

        fig_bar, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig_bar.patch.set_facecolor(BG_COLOR)
        for ax in axes:
            style_ax(ax)

        axes[0].bar(class_avg.index, class_avg["TotalSteps"], color=CHART_COLORS)
        axes[0].set_title("Avg Daily Steps")
        axes[0].set_xlabel("User Class")
        axes[0].set_ylabel("Steps")
        for i, v in enumerate(class_avg["TotalSteps"]):
            axes[0].text(i, v + 100, f"{int(v):,}", ha="center", fontsize=10, color="white")

        axes[1].bar(class_avg.index, class_avg["Calories"], color=CHART_COLORS)
        axes[1].set_title("Avg Daily Calories")
        axes[1].set_xlabel("User Class")
        axes[1].set_ylabel("Calories")
        for i, v in enumerate(class_avg["Calories"]):
            axes[1].text(i, v + 5, f"{int(v):,}", ha="center", fontsize=10, color="white")

        plt.tight_layout()
        st.pyplot(fig_bar)

# ── Tab 2: Leaderboard ────────────────────────────────────────────────────────
with tab_leaderboard:

    user_avg = (
        df_overview.groupby("Id")
        .agg(
            avg_steps=("TotalSteps", "mean"),
            avg_calories=("Calories", "mean"),
            days_recorded=("TotalSteps", "count"),
            user_class=("Class", "first"),
        )
        .round(0)
        .astype({"avg_steps": int, "avg_calories": int})
        .reset_index()
        .sort_values("avg_steps", ascending=False)
    )
    user_avg.insert(0, "Rank", range(1, len(user_avg) + 1))
    user_avg = user_avg.rename(columns={
        "Id":            "User ID",
        "avg_steps":     "Avg Daily Steps",
        "avg_calories":  "Avg Daily Calories",
        "days_recorded": "Days Recorded",
        "user_class":    "Class",
    })

    top5    = user_avg.head(5).set_index("Rank")
    bottom5 = user_avg.tail(5).sort_values("Avg Daily Steps").set_index("Rank")

    col_top, col_bot = st.columns(2)
    with col_top:
        with st.container(border=True):
            st.markdown("**Most active**")
            st.dataframe(top5, use_container_width=True)
    with col_bot:
        with st.container(border=True):
            st.markdown("**Least active**")
            st.dataframe(bottom5, use_container_width=True)

    with st.container(border=True):
        st.markdown("**Full ranking**")
        st.dataframe(user_avg.set_index("Rank"), use_container_width=True)

# ── Tab 3: Weekday Patterns ───────────────────────────────────────────────────
with tab_weekday:

    with st.container(border=True):
        activity_metric = st.selectbox("Metric", [
            "TotalSteps", "TotalDistance", "VeryActiveMinutes", "FairlyActiveMinutes",
            "LightlyActiveMinutes", "SedentaryMinutes", "Calories"
        ])
        fig_box, conclusion = plot_weekday_activity_per_class(df=df_activity.copy(), variable=activity_metric)
        st.pyplot(fig_box)
        st.caption(conclusion)
