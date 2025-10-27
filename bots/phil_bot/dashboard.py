import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from collections import Counter
import os
from pathlib import Path
from dotenv import load_dotenv
from bson import ObjectId
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import hashlib

# Load environment variables
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=ROOT / ".env")
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env.local", override=True)

# Page config
st.set_page_config(
    page_title="Nomos Bot Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# MongoDB setup
@st.cache_resource
def init_connection():
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(MONGODB_URI)
    return client


client = init_connection()
db = client["study_chatbot"]
conversations_col = db["conversations"]
feedback_col = db["feedback"]
users_col = db["users"]


# Utility functions
def anonymize_email(email):
    """Convert email to a consistent hash for privacy."""
    if pd.isna(email) or email is None:
        return "unknown"
    return hashlib.sha256(str(email).encode()).hexdigest()[:8]


def count_words(text):
    """Count words in a text string."""
    if not text:
        return 0
    return len(text.split())


def extract_keywords(messages, top_n=20):
    """Extract common words from messages, filtering stopwords."""
    german_stopwords = {
        "der",
        "die",
        "das",
        "und",
        "oder",
        "aber",
        "in",
        "zu",
        "mit",
        "von",
        "auf",
        "für",
        "ist",
        "sind",
        "nicht",
        "ein",
        "eine",
        "ich",
        "du",
        "er",
        "sie",
        "es",
        "wir",
        "ihr",
        "den",
        "dem",
        "des",
        "im",
        "am",
        "zum",
        "zur",
        "was",
        "wie",
        "wo",
        "wenn",
        "kann",
        "kannst",
        "können",
        "habe",
        "hat",
        "haben",
        "wird",
        "wurde",
        "werden",
        "sein",
        "war",
        "dass",
        "dein",
        "mir",
        "mich",
    }

    words = []
    for msg in messages:
        if isinstance(msg, str):
            # Remove special characters and split
            text = re.sub(r"[^\w\s]", " ", msg.lower())
            words.extend(
                [w for w in text.split() if len(w) > 3 and w not in german_stopwords]
            )

    return Counter(words).most_common(top_n)


# Data loading functions with caching
@st.cache_data(ttl=60)
def load_users():
    """Load all users data."""
    users = list(users_col.find())
    if not users:
        return pd.DataFrame()
    df = pd.DataFrame(users)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
    if "last_login_at" in df.columns:
        df["last_login_at"] = pd.to_datetime(df["last_login_at"])
    return df


@st.cache_data(ttl=60)
def load_conversations():
    """Load all conversations data."""
    convs = list(conversations_col.find())
    if not convs:
        return pd.DataFrame()

    df = pd.DataFrame(convs)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["last_updated"] = pd.to_datetime(df["last_updated"])

    # Calculate metrics
    df["num_messages"] = df["messages"].apply(len)
    df["user_messages"] = df["messages"].apply(
        lambda msgs: [m for m in msgs if m.get("role") == "user"]
    )
    df["assistant_messages"] = df["messages"].apply(
        lambda msgs: [m for m in msgs if m.get("role") == "assistant"]
    )
    df["num_user_messages"] = df["user_messages"].apply(len)
    df["num_assistant_messages"] = df["assistant_messages"].apply(len)

    # Word counts
    df["user_words_total"] = df["user_messages"].apply(
        lambda msgs: sum(count_words(m.get("content", "")) for m in msgs)
    )
    df["assistant_words_total"] = df["assistant_messages"].apply(
        lambda msgs: sum(count_words(m.get("content", "")) for m in msgs)
    )
    df["avg_user_words"] = df.apply(
        lambda row: row["user_words_total"] / row["num_user_messages"]
        if row["num_user_messages"] > 0
        else 0,
        axis=1,
    )
    df["avg_assistant_words"] = df.apply(
        lambda row: row["assistant_words_total"] / row["num_assistant_messages"]
        if row["num_assistant_messages"] > 0
        else 0,
        axis=1,
    )

    # Duration
    df["duration_hours"] = (
        df["last_updated"] - df["created_at"]
    ).dt.total_seconds() / 3600

    return df


@st.cache_data(ttl=60)
def load_feedback():
    """Load all feedback data."""
    fb = list(feedback_col.find())
    if not fb:
        return pd.DataFrame()
    df = pd.DataFrame(fb)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


# Authentication check
def check_admin_access():
    """Simple admin authentication."""
    admin_emails = os.getenv("DASHBOARD_ADMIN_EMAILS", "").split(",")
    admin_emails = [e.strip() for e in admin_emails if e.strip()]

    if not admin_emails:
        # No restriction if not configured
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Admin Authentication Required")
        email = st.text_input("Enter admin email:", key="admin_email")
        if st.button("Access Dashboard"):
            if email in admin_emails:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access denied. Invalid admin email.")
        st.stop()

    return True


# Main app
def main():
    check_admin_access()

    st.title("📊 Nomos Bot Analytics Dashboard")
    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.header("Filters & Settings")

        # Privacy toggle
        anonymize = st.checkbox("Anonymize user emails", value=True)

        # Consent filter
        consent_filter = st.selectbox(
            "Filter by research consent:",
            ["All users", "Consented only", "Not consented", "No response"],
        )

        # Date range
        st.subheader("Date Range")
        use_date_filter = st.checkbox("Apply date filter", value=False)
        if use_date_filter:
            date_from = st.date_input(
                "From:", value=datetime.now() - timedelta(days=30)
            )
            date_to = st.date_input("To:", value=datetime.now())

        st.markdown("---")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Load data
    users_df = load_users()
    convs_df = load_conversations()
    feedback_df = load_feedback()

    # Apply consent filter to conversations
    if not users_df.empty and not convs_df.empty and consent_filter != "All users":
        consent_map = dict(
            zip(users_df["email"], users_df.get("consent_research", None))
        )

        if consent_filter == "Consented only":
            convs_df = convs_df[
                convs_df["user"].map(lambda u: consent_map.get(u) == True)
            ]
        elif consent_filter == "Not consented":
            convs_df = convs_df[
                convs_df["user"].map(lambda u: consent_map.get(u) == False)
            ]
        elif consent_filter == "No response":
            convs_df = convs_df[
                convs_df["user"].map(lambda u: consent_map.get(u) is None)
            ]

    # Apply date filter
    if use_date_filter and not convs_df.empty:
        date_from_dt = pd.Timestamp(date_from)
        date_to_dt = pd.Timestamp(date_to) + pd.Timedelta(days=1)
        convs_df = convs_df[
            (convs_df["created_at"] >= date_from_dt)
            & (convs_df["created_at"] < date_to_dt)
        ]

    # Create tabs
    tabs = st.tabs(
        [
            "📈 Overview",
            "👥 User Growth",
            "📅 Daily Activity",
            "💬 Conversation Analytics",
            "🔍 Topic Analysis",
            "📖 Conversation Viewer",
            "⭐ Feedback",
        ]
    )

    # Tab 1: Overview
    with tabs[0]:
        render_overview_tab(users_df, convs_df, feedback_df, anonymize)

    # Tab 2: User Growth
    with tabs[1]:
        render_user_growth_tab(users_df, anonymize)

    # Tab 3: Daily Activity
    with tabs[2]:
        render_daily_activity_tab(users_df, convs_df, anonymize)

    # Tab 4: Conversation Analytics
    with tabs[3]:
        render_conversation_analytics_tab(convs_df)

    # Tab 5: Topic Analysis
    with tabs[4]:
        render_topic_analysis_tab(convs_df)

    # Tab 6: Conversation Viewer
    with tabs[5]:
        render_conversation_viewer_tab(convs_df, feedback_df, anonymize)

    # Tab 7: Feedback
    with tabs[6]:
        render_feedback_tab(feedback_df, convs_df, anonymize)


def render_overview_tab(users_df, convs_df, feedback_df, anonymize):
    """Render the overview tab with high-level metrics."""
    st.header("Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_users = len(users_df) if not users_df.empty else 0
        st.metric("Total Users", total_users)
        if not users_df.empty and "consent_research" in users_df.columns:
            consented = users_df["consent_research"].sum()
            st.caption(f"{consented} consented to research")

    with col2:
        total_convs = len(convs_df) if not convs_df.empty else 0
        st.metric("Total Conversations", total_convs)
        if not convs_df.empty:
            avg_per_user = total_convs / total_users if total_users > 0 else 0
            st.caption(f"{avg_per_user:.1f} per user avg")

    with col3:
        total_messages = convs_df["num_messages"].sum() if not convs_df.empty else 0
        st.metric("Total Messages", int(total_messages))
        if not convs_df.empty and total_convs > 0:
            avg_per_conv = total_messages / total_convs
            st.caption(f"{avg_per_conv:.1f} per conversation avg")

    with col4:
        if not feedback_df.empty and "rating" in feedback_df.columns:
            avg_rating = feedback_df["rating"].mean()
            st.metric("Average Rating", f"{avg_rating:.2f}/5")
            st.caption(f"Based on {len(feedback_df)} ratings")
        else:
            st.metric("Average Rating", "N/A")

    st.markdown("---")

    # Recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent User Registrations")
        if not users_df.empty and "created_at" in users_df.columns:
            recent_users = users_df.nlargest(10, "created_at")[["email", "created_at"]]
            if anonymize:
                recent_users["email"] = recent_users["email"].apply(anonymize_email)
            recent_users["created_at"] = recent_users["created_at"].dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            st.dataframe(recent_users, use_container_width=True, hide_index=True)
        else:
            st.info("No user data available")

    with col2:
        st.subheader("Recent Conversations")
        if not convs_df.empty:
            recent_convs = convs_df.nlargest(10, "created_at")[
                ["user", "title", "num_messages", "created_at"]
            ]
            if anonymize:
                recent_convs["user"] = recent_convs["user"].apply(anonymize_email)
            recent_convs["created_at"] = recent_convs["created_at"].dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            st.dataframe(recent_convs, use_container_width=True, hide_index=True)
        else:
            st.info("No conversation data available")


def render_user_growth_tab(users_df, anonymize):
    """Render user growth analytics."""
    st.header("User Growth")

    if users_df.empty or "created_at" not in users_df.columns:
        st.info("No user data available")
        return

    # Cumulative users over time
    st.subheader("Cumulative Users Over Time")
    users_by_date = users_df.set_index("created_at").resample("D").size().cumsum()
    fig = px.line(
        users_by_date,
        title="Total Users (Cumulative)",
        labels={"value": "Total Users", "created_at": "Date"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # New users per period
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("New Users per Day")
        new_users_daily = users_df.set_index("created_at").resample("D").size()
        fig = px.bar(
            new_users_daily,
            title="Daily New Registrations",
            labels={"value": "New Users", "created_at": "Date"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("New Users per Week")
        new_users_weekly = users_df.set_index("created_at").resample("W").size()
        fig = px.bar(
            new_users_weekly,
            title="Weekly New Registrations",
            labels={"value": "New Users", "created_at": "Week"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # Consent breakdown
    st.subheader("Research Consent Breakdown")
    if "consent_research" in users_df.columns:
        consent_counts = users_df["consent_research"].value_counts()
        consent_labels = {True: "Consented", False: "Declined", None: "No Response"}
        consent_data = pd.DataFrame(
            {
                "Status": [
                    consent_labels.get(k, "Unknown") for k in consent_counts.index
                ],
                "Count": consent_counts.values,
            }
        )

        fig = px.pie(
            consent_data,
            values="Count",
            names="Status",
            title="Research Consent Status",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No consent data available")

    # User table
    st.subheader("All Users")
    user_table = users_df[
        ["email", "created_at", "last_login_at", "consent_research"]
    ].copy()
    if anonymize:
        user_table["email"] = user_table["email"].apply(anonymize_email)
    user_table = user_table.sort_values("created_at", ascending=False)
    user_table["created_at"] = user_table["created_at"].dt.strftime("%Y-%m-%d %H:%M")
    if "last_login_at" in user_table.columns:
        user_table["last_login_at"] = user_table["last_login_at"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )
    st.dataframe(user_table, use_container_width=True, hide_index=True)


def render_daily_activity_tab(users_df, convs_df, anonymize):
    """Render daily activity metrics."""
    st.header("Daily Activity")

    if convs_df.empty:
        st.info("No conversation data available")
        return

    # Unique active users per day
    st.subheader("Unique Active Users per Day")
    convs_df["date"] = convs_df["created_at"].dt.date
    active_users_daily = convs_df.groupby("date")["user"].nunique()
    fig = px.line(
        active_users_daily,
        title="Daily Active Users",
        labels={"value": "Unique Users", "date": "Date"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # New conversations per day
    st.subheader("New Conversations per Day")
    convs_daily = convs_df.groupby("date").size()
    fig = px.bar(
        convs_daily,
        title="Daily New Conversations",
        labels={"value": "Conversations", "date": "Date"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Activity heatmap (day of week vs hour)
    st.subheader("Activity Heatmap (Day of Week vs Hour)")
    convs_df["hour"] = convs_df["created_at"].dt.hour
    convs_df["day_of_week"] = convs_df["created_at"].dt.day_name()

    # Create heatmap data
    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    heatmap_data = (
        convs_df.groupby(["day_of_week", "hour"]).size().unstack(fill_value=0)
    )
    heatmap_data = heatmap_data.reindex(day_order)

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale="Blues",
            hoverongaps=False,
        )
    )
    fig.update_layout(
        title="Conversation Start Times",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Most active users
    st.subheader("Most Active Users")
    user_activity = (
        convs_df.groupby("user")
        .agg({"_id": "count", "num_messages": "sum", "created_at": ["min", "max"]})
        .round(2)
    )
    user_activity.columns = [
        "Conversations",
        "Total Messages",
        "First Activity",
        "Last Activity",
    ]
    user_activity = user_activity.sort_values("Conversations", ascending=False).head(20)

    if anonymize:
        user_activity.index = [anonymize_email(email) for email in user_activity.index]

    user_activity["First Activity"] = pd.to_datetime(
        user_activity["First Activity"]
    ).dt.strftime("%Y-%m-%d")
    user_activity["Last Activity"] = pd.to_datetime(
        user_activity["Last Activity"]
    ).dt.strftime("%Y-%m-%d")
    st.dataframe(user_activity, use_container_width=True)


def render_conversation_analytics_tab(convs_df):
    """Render conversation-level analytics."""
    st.header("Conversation Analytics")

    if convs_df.empty:
        st.info("No conversation data available")
        return

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Messages/Conv", f"{convs_df['num_messages'].mean():.1f}")
    with col2:
        st.metric("Median Messages/Conv", f"{convs_df['num_messages'].median():.0f}")
    with col3:
        st.metric("Avg Duration (hours)", f"{convs_df['duration_hours'].mean():.2f}")
    with col4:
        st.metric(
            "Median Duration (hours)", f"{convs_df['duration_hours'].median():.2f}"
        )

    st.markdown("---")

    # Distribution plots
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Conversation Length Distribution")
        fig = px.histogram(
            convs_df,
            x="num_messages",
            nbins=30,
            title="Distribution of Messages per Conversation",
            labels={"num_messages": "Number of Messages"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Conversation Duration Distribution")
        # Filter out very long durations (likely inactive sessions)
        duration_filtered = convs_df[convs_df["duration_hours"] <= 24]
        fig = px.histogram(
            duration_filtered,
            x="duration_hours",
            nbins=30,
            title="Distribution of Conversation Duration (≤24h)",
            labels={"duration_hours": "Duration (hours)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # User vs Assistant message lengths
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("User Message Length (avg words)")
        fig = px.histogram(
            convs_df,
            x="avg_user_words",
            nbins=30,
            title="Average Words per User Message",
            labels={"avg_user_words": "Average Words"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Assistant Message Length (avg words)")
        fig = px.histogram(
            convs_df,
            x="avg_assistant_words",
            nbins=30,
            title="Average Words per Assistant Message",
            labels={"avg_assistant_words": "Average Words"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # Box plot comparison
    st.subheader("User vs Assistant Message Length Comparison")
    comparison_data = pd.DataFrame(
        {
            "User": convs_df["avg_user_words"],
            "Assistant": convs_df["avg_assistant_words"],
        }
    )
    fig = px.box(
        comparison_data,
        title="Distribution of Average Words per Message",
        labels={"value": "Average Words", "variable": "Role"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.subheader("Conversation Statistics Summary")
    summary = pd.DataFrame(
        {
            "Metric": [
                "Total Conversations",
                "Total Messages",
                "Total User Messages",
                "Total Assistant Messages",
                "Avg Messages per Conversation",
                "Avg User Messages per Conversation",
                "Avg Assistant Messages per Conversation",
                "Avg User Words per Message",
                "Avg Assistant Words per Message",
                "Avg Duration (hours)",
            ],
            "Value": [
                len(convs_df),
                convs_df["num_messages"].sum(),
                convs_df["num_user_messages"].sum(),
                convs_df["num_assistant_messages"].sum(),
                f"{convs_df['num_messages'].mean():.1f}",
                f"{convs_df['num_user_messages'].mean():.1f}",
                f"{convs_df['num_assistant_messages'].mean():.1f}",
                f"{convs_df['avg_user_words'].mean():.1f}",
                f"{convs_df['avg_assistant_words'].mean():.1f}",
                f"{convs_df['duration_hours'].mean():.2f}",
            ],
        }
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)


def render_topic_analysis_tab(convs_df):
    """Render topic analysis with word clouds and keywords."""
    st.header("Topic Analysis")

    if convs_df.empty:
        st.info("No conversation data available")
        return

    # Extract all user messages
    all_user_messages = []
    for msgs in convs_df["user_messages"]:
        all_user_messages.extend([m.get("content", "") for m in msgs])

    if not all_user_messages:
        st.info("No user messages available for analysis")
        return

    # Word cloud
    st.subheader("Word Cloud from User Messages")
    text = " ".join(all_user_messages)

    # German stopwords
    german_stopwords = {
        "der",
        "die",
        "das",
        "und",
        "oder",
        "aber",
        "in",
        "zu",
        "mit",
        "von",
        "auf",
        "für",
        "ist",
        "sind",
        "nicht",
        "ein",
        "eine",
        "ich",
        "du",
        "er",
        "sie",
        "es",
        "wir",
        "ihr",
        "den",
        "dem",
        "des",
        "im",
        "am",
        "zum",
        "zur",
        "was",
        "wie",
        "wo",
        "wenn",
        "kann",
        "kannst",
        "können",
        "habe",
        "hat",
        "haben",
        "wird",
        "wurde",
        "werden",
        "sein",
        "war",
        "dass",
        "dein",
        "mir",
        "mich",
        "bei",
        "durch",
        "nach",
        "aus",
        "über",
        "auch",
        "noch",
        "nur",
        "so",
        "dann",
        "doch",
        "mehr",
        "schon",
        "sehr",
        "hier",
        "da",
    }

    try:
        wordcloud = WordCloud(
            width=1200,
            height=600,
            background_color="white",
            stopwords=german_stopwords,
            colormap="viridis",
            max_words=100,
        ).generate(text)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Could not generate word cloud: {e}")

    # Top keywords
    st.subheader("Top Keywords from User Messages")
    keywords = extract_keywords(all_user_messages, top_n=30)

    col1, col2 = st.columns(2)

    with col1:
        # Table
        keywords_df = pd.DataFrame(keywords, columns=["Keyword", "Frequency"])
        st.dataframe(keywords_df, use_container_width=True, hide_index=True)

    with col2:
        # Bar chart
        fig = px.bar(
            keywords_df.head(20),
            x="Frequency",
            y="Keyword",
            orientation="h",
            title="Top 20 Keywords by Frequency",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    # Message role breakdown
    st.subheader("Message Distribution by Role")
    total_user_msgs = convs_df["num_user_messages"].sum()
    total_assistant_msgs = convs_df["num_assistant_messages"].sum()

    role_data = pd.DataFrame(
        {
            "Role": ["User", "Assistant"],
            "Messages": [total_user_msgs, total_assistant_msgs],
        }
    )

    fig = px.pie(
        role_data,
        values="Messages",
        names="Role",
        title="Distribution of Messages by Role",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_conversation_viewer_tab(convs_df, feedback_df, anonymize):
    """Render conversation viewer with search and display."""
    st.header("Conversation Viewer")

    if convs_df.empty:
        st.info("No conversation data available")
        return

    # Filters
    st.subheader("Search & Filter")
    col1, col2, col3 = st.columns(3)

    with col1:
        users = ["All"] + sorted(convs_df["user"].unique().tolist())
        if anonymize:
            user_display = ["All"] + [anonymize_email(u) for u in users[1:]]
            selected_user_display = st.selectbox("Filter by user:", user_display)
            selected_user = (
                users[user_display.index(selected_user_display)]
                if selected_user_display != "All"
                else "All"
            )
        else:
            selected_user = st.selectbox("Filter by user:", users)

    with col2:
        min_messages = st.number_input("Min messages:", min_value=0, value=0)

    with col3:
        sort_by = st.selectbox(
            "Sort by:", ["created_at", "last_updated", "num_messages"], index=0
        )
        sort_order = st.radio("Order:", ["Descending", "Ascending"], horizontal=True)

    # Apply filters
    filtered_df = convs_df.copy()
    if selected_user != "All":
        filtered_df = filtered_df[filtered_df["user"] == selected_user]
    if min_messages > 0:
        filtered_df = filtered_df[filtered_df["num_messages"] >= min_messages]

    filtered_df = filtered_df.sort_values(
        sort_by, ascending=(sort_order == "Ascending")
    )

    st.info(f"Showing {len(filtered_df)} conversation(s)")

    # Conversation list
    st.subheader("Conversations")

    # Create display dataframe
    display_df = filtered_df[
        ["_id", "user", "title", "num_messages", "created_at", "last_updated"]
    ].copy()
    display_df["_id_str"] = display_df["_id"].astype(str)
    if anonymize:
        display_df["user"] = display_df["user"].apply(anonymize_email)
    display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M")
    display_df["last_updated"] = display_df["last_updated"].dt.strftime(
        "%Y-%m-%d %H:%M"
    )

    # Select conversation
    if not filtered_df.empty:
        # Show table with selection
        selection_df = display_df[
            ["_id_str", "user", "title", "num_messages", "created_at"]
        ].copy()
        selection_df.columns = ["ID", "User", "Title", "Messages", "Created"]

        st.dataframe(selection_df, use_container_width=True, hide_index=True)

        # Select by ID
        conv_id_input = st.text_input("Enter conversation ID to view:", key="conv_id")

        if conv_id_input:
            try:
                selected_conv = filtered_df[
                    filtered_df["_id"].astype(str) == conv_id_input
                ]
                if not selected_conv.empty:
                    render_single_conversation(
                        selected_conv.iloc[0], feedback_df, anonymize
                    )
                else:
                    st.warning("Conversation not found in filtered results")
            except Exception as e:
                st.error(f"Error loading conversation: {e}")


def render_single_conversation(conv, feedback_df, anonymize):
    """Render a single conversation with full details."""
    st.markdown("---")
    st.subheader("Conversation Details")

    # Metadata
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        user_display = anonymize_email(conv["user"]) if anonymize else conv["user"]
        st.write(f"**User:** {user_display}")
    with col2:
        st.write(f"**Created:** {conv['created_at'].strftime('%Y-%m-%d %H:%M')}")
    with col3:
        st.write(f"**Last Updated:** {conv['last_updated'].strftime('%Y-%m-%d %H:%M')}")
    with col4:
        st.write(f"**Messages:** {conv['num_messages']}")

    st.write(f"**Title:** {conv.get('title', 'Untitled')}")

    # Associated feedback
    conv_id_str = str(conv["_id"])
    if not feedback_df.empty:
        conv_feedback = feedback_df[feedback_df["conversation_id"] == conv_id_str]
        if not conv_feedback.empty:
            st.info(f"⭐ Rating: {conv_feedback.iloc[0]['rating']}/5")
            if conv_feedback.iloc[0].get("feedback"):
                st.write(f"**Feedback:** {conv_feedback.iloc[0]['feedback']}")

    # Messages
    st.subheader("Messages")
    messages = conv["messages"]

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)
        else:
            st.text(f"[{role}]: {content}")

    # Export options
    st.subheader("Export")
    col1, col2 = st.columns(2)

    with col1:
        # JSON export
        export_data = {
            "conversation_id": conv_id_str,
            "user": conv["user"],
            "title": conv.get("title", ""),
            "created_at": conv["created_at"].isoformat(),
            "last_updated": conv["last_updated"].isoformat(),
            "messages": messages,
        }
        st.download_button(
            "Download as JSON",
            data=pd.io.json.dumps(export_data, indent=2),
            file_name=f"conversation_{conv_id_str}.json",
            mime="application/json",
        )

    with col2:
        # Text export
        text_export = f"Conversation: {conv.get('title', 'Untitled')}\n"
        text_export += f"User: {conv['user']}\n"
        text_export += f"Created: {conv['created_at']}\n\n"
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            text_export += f"[{role}]\n{content}\n\n"

        st.download_button(
            "Download as Text",
            data=text_export,
            file_name=f"conversation_{conv_id_str}.txt",
            mime="text/plain",
        )


def render_feedback_tab(feedback_df, convs_df, anonymize):
    """Render feedback analytics."""
    st.header("Feedback Analytics")

    if feedback_df.empty:
        st.info("No feedback data available")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Feedback", len(feedback_df))

    with col2:
        avg_rating = feedback_df["rating"].mean()
        st.metric("Average Rating", f"{avg_rating:.2f}/5")

    with col3:
        median_rating = feedback_df["rating"].median()
        st.metric("Median Rating", f"{median_rating:.1f}/5")

    with col4:
        with_text = feedback_df["feedback"].notna().sum()
        st.metric("With Text Comments", with_text)

    # Rating distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Rating Distribution")
        rating_counts = feedback_df["rating"].value_counts().sort_index()
        fig = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            labels={"x": "Rating", "y": "Count"},
            title="Distribution of Ratings",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Ratings Over Time")
        if "created_at" in feedback_df.columns:
            feedback_df_sorted = feedback_df.sort_values("created_at")
            fig = px.scatter(
                feedback_df_sorted,
                x="created_at",
                y="rating",
                title="Ratings Timeline",
                labels={"created_at": "Date", "rating": "Rating"},
            )
            # Add trend line
            fig.add_trace(
                go.Scatter(
                    x=feedback_df_sorted["created_at"],
                    y=feedback_df_sorted["rating"]
                    .rolling(window=5, min_periods=1)
                    .mean(),
                    mode="lines",
                    name="Moving Average (5)",
                    line=dict(color="red", dash="dash"),
                )
            )
            st.plotly_chart(fig, use_container_width=True)

    # Word cloud from feedback text
    if feedback_df["feedback"].notna().sum() > 0:
        st.subheader("Word Cloud from Feedback Comments")
        feedback_texts = feedback_df[feedback_df["feedback"].notna()][
            "feedback"
        ].tolist()
        text = " ".join(feedback_texts)

        german_stopwords = {
            "der",
            "die",
            "das",
            "und",
            "oder",
            "aber",
            "in",
            "zu",
            "mit",
            "von",
            "auf",
            "für",
            "ist",
            "sind",
            "nicht",
            "ein",
            "eine",
        }

        try:
            wordcloud = WordCloud(
                width=1200,
                height=400,
                background_color="white",
                stopwords=german_stopwords,
                colormap="plasma",
                max_words=50,
            ).generate(text)

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Could not generate word cloud: {e}")

    # Feedback table
    st.subheader("All Feedback")
    display_feedback = feedback_df[["user", "rating", "feedback", "created_at"]].copy()
    if anonymize:
        display_feedback["user"] = display_feedback["user"].apply(anonymize_email)
    if "created_at" in display_feedback.columns:
        display_feedback["created_at"] = display_feedback["created_at"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )
    display_feedback = (
        display_feedback.sort_values("created_at", ascending=False)
        if "created_at" in display_feedback.columns
        else display_feedback
    )
    st.dataframe(display_feedback, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
