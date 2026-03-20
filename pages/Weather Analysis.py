import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3
from scipy.stats import pearsonr
import seaborn as sns

# === Page config ===
st.set_page_config(
    page_title="Weather Analysis",
    page_icon="fitbit",
    layout="wide",
    initial_sidebar_state="expanded"
)

BG_COLOR = "#111420"
C_BLUE = "#4C9BE8"
C_ORANGE = "#E8834C"
C_GREEN = "#52C97A"
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

weather = pd.read_csv("data/ChicagoWeather.csv")
weather['datetime'] = pd.to_datetime(weather['datetime'], format="%Y-%m-%d")
weather = weather[['datetime', 'temp', 'precip', 'windspeed', "feelslike", "humidity"]]

df_activity = load_activity_data()

df_activity["Id"] = df_activity["Id"].astype("int64")
df_activity["ActivityDate"] = pd.to_datetime(df_activity["ActivityDate"], format="%m/%d/%Y")

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

merged_df_weather = activity_daily.merge(weather, left_on="ActivityDate", right_on="datetime", how="left")
activity_vars = [
    "TotalSteps", "VeryActiveMinutes", "FairlyActiveMinutes",
    "LightlyActiveMinutes", "SedentaryMinutes", "Calories",
    "TotalDistance", "ModeratelyActiveDistance",
    "LightActiveDistance", "SedentaryActiveDistance"
]

weather_vars = ["temp", "precip", "windspeed", 'feelslike', 'humidity']

def plot_weather_act( x, y,df=merged_df_weather, color=C_BLUE):
    fig, ax = plt.subplots(figsize=(8, 5))

    # Background styling
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Regression plot
    sns.regplot(
        data=df,
        x=x,
        y=y,
        ax=ax,
        scatter_kws={"color": color},
        line_kws={"color": color}
    )

    # Make labels readable on dark background
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")

    return fig

# === Sidebar ===
st.sidebar.markdown(
    """
    <div style="padding: 12px 4px 8px 4px;">
        <div style="color:white; font-size:1.1rem; font-weight:700; margin-bottom:4px;">Weather Analysis</div>
        <div style="color:#9B9EAC; font-size:0.78rem; line-height:1.5;">
            How weather conditions relate to group activity levels.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()
st.sidebar.markdown("**Select a Weather variable**")
chosen_weather_var = st.sidebar.selectbox("Select a User ID", weather_vars)

st.sidebar.markdown("---")
st.sidebar.markdown("**Select a Activity variable**")
chosen_activity_var = st.sidebar.selectbox("Select an Activity Variable", activity_vars)

# Page header
st.title("Relationship between Activity and Weather")
st.caption(f"{chosen_weather_var} vs. {chosen_activity_var}")
st.divider()

with st.container(border=True):
    fig_steps = plot_weather_act(x=chosen_activity_var, y=chosen_weather_var)        
    if fig_steps is not None:
            st.pyplot(fig_steps)

from scipy.stats import pearsonr
import streamlit as st

r, p = pearsonr(
    merged_df_weather[chosen_weather_var],
    merged_df_weather[chosen_activity_var]
)

with st.container(border=True):
    st.markdown("**Group Comparison**. Note that there are more than 30 data points. Central limit theorem justifies the use of parametric Pearson's r.")

    col_r, col_p = st.columns(2)

    # --- Column for r ---
    with col_r:
        st.markdown("### r-value")
        st.markdown(f"<h2 style='color:white;'>{r:.3f}</h2>", unsafe_allow_html=True)

    # --- Column for p ---
    with col_p:
        st.markdown("### p-value")

        # Color logic
        p_color = "green" if p < 0.05 else "red"

        st.markdown(
            f"<h2 style='color:{p_color};'>{p:.3f}</h2>",
            unsafe_allow_html=True
        )

        if p < 0.05:
            st.caption("Yay! There must be something! Be mindful that this p-value was not corrected and be mindful of the effect size")
        else:
            st.caption("Seems like people don't really care about weather!")