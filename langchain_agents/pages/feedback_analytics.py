import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import toml
from pathlib import Path

# Load secrets
secrets_path = Path(__file__).parent.parent.parent / "secrets.toml"
secrets = toml.load(str(secrets_path))
DB_URL = secrets['POSTGRES_DB']

def load_feedback_data():
    """Load feedback data from PostgreSQL database."""
    try:
        with psycopg2.connect(DB_URL) as conn:
            query = """
                SELECT 
                    timestamp,
                    user_id,
                    rating,
                    feedback_text,
                    user_input,
                    agent_response
                FROM agent_feedback
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, conn)
            # Convert rating column to numeric
            df['rating'] = pd.to_numeric(df['rating'])
            df['rating'] = df['rating'] + 1
            return df
    except Exception as e:
        st.error(f"Error loading feedback data: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("📊 Feedback Analytics")
    
    # Load data
    df = load_feedback_data()
    
    if df.empty:
        st.warning("No feedback data available")
        return
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Feedback Count", len(df))
    
    with col2:
        avg_rating = df['rating'].mean()
        st.metric("Average Rating (1-5)", f"{avg_rating:.2f}")
    
    with col3:
        unique_users = df['user_id'].nunique()
        st.metric("Unique Users", unique_users)
    
    # Rating distribution plot
    st.subheader("🌟 Rating Distribution (1-5)")
    rating_counts = df['rating'].value_counts().reset_index()
    rating_counts.columns = ['Rating', 'Count']
    
    fig = px.bar(
        rating_counts,
        x='Rating',
        y='Count',
        title='Distribution of Feedback Ratings (1-5)',
        color='Rating'
    )
    st.plotly_chart(fig)
    
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_feedback = df.groupby('date').size().reset_index()
    daily_feedback.columns = ['Date', 'Count']
    
    # Recent feedback table
    st.subheader("📝 Recent Feedback")
    
    # Format the dataframe for display
    display_df = df[['timestamp', 'rating', 'feedback_text', 'user_input', 'agent_response']].copy()
    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Create an expander for each feedback entry
    for idx, row in display_df.iterrows():
        with st.expander(f"Feedback from {row['timestamp']} - Rating: {row['rating']}"):
            st.write("**User Question:**")
            st.write(row['user_input'])
            st.write("**Agent Response:**")
            st.write(row['agent_response'])
            st.write("**Feedback:**")
            st.write(row['feedback_text'])

if __name__ == "__main__":
    main() 