import streamlit as st
import asyncio
from agent import JobApplicationAgent
import toml
import os
from typing import BinaryIO
import pymupdf
import pandas as pd
from pathlib import Path
import uuid
import psycopg2
from datetime import datetime
from streamlit_option_menu import option_menu

# Initialize environment variables and configurations
try:
    # save in secrets.toml in the root directory (not .streamlit)
    secrets_path = Path(__file__).parent.parent / "secrets.toml"
    secrets = toml.load(str(secrets_path))
    os.environ['TOGETHER_API_KEY'] = secrets['TOGETHER_API_KEY']
except Exception as e:
    st.error(f"Error loading secrets: {str(e)}")
    st.stop()

def get_pdf_text(pdf_file: BinaryIO) -> str:
    """Extract text from a PDF file."""
    pdf = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
    text = ''
    for page in pdf.pages():
        text += page.get_text()
    return text

class StreamlitUI:
    def __init__(self):
        # Add user session tracking
        if 'user_id' not in st.session_state:
            st.session_state.user_id = self.generate_user_id()
        
        # Initialize session state
        if 'agent' not in st.session_state:
            st.session_state.agent = asyncio.run(self.initialize_agent())
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            # Add welcome message to chat history
            welcome_message = """👋 Welcome to RecruiTree 🌲! I'm here to help you create unique professional presence to get RecruiTree'd .

To get started:
1. Upload your resume (PDF) using the panel on the right
2. Try asking me to:
   - Create a personal website/portfolio 🌐
   - Improve your GitHub profile 🔍
   - Create a cool and fancy GitHub README 📝

How can I help you?"""
            st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
            # Force a rerun to display the welcome message
            st.rerun()
        
        if 'uploaded_resume' not in st.session_state:
            st.session_state.uploaded_resume = None
        
        # Use the connection string directly instead of separate parameters
        self.db_url = secrets['POSTGRES_DB']
        
        # Initialize database table if it doesn't exist
        self.initialize_database()
        
        # Add a new session state variable to track submitted feedback
        if 'submitted_feedbacks' not in st.session_state:
            st.session_state.submitted_feedbacks = set()
    
    @staticmethod
    async def initialize_agent() -> JobApplicationAgent:
        """Initialize the agent asynchronously."""
        return JobApplicationAgent()
            
    def initialize_database(self):
        """Initialize the PostgreSQL database and create table if it doesn't exist."""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS agent_feedback (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP,
                            user_id TEXT,
                            chat_history TEXT,
                            user_input TEXT,
                            agent_response TEXT,
                            rating TEXT,
                            feedback_text TEXT
                        )
                    """)
                conn.commit()
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")

    def save_feedback(self, feedback_data: dict):
        """Save feedback to PostgreSQL database."""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO agent_feedback 
                        (timestamp, user_id, chat_history, user_input, agent_response, rating, feedback_text)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        datetime.now(),
                        feedback_data['user_id'],
                        feedback_data['chat_history'],
                        feedback_data['user_input'],
                        feedback_data['agent_response'],
                        feedback_data['rating'],
                        feedback_data['feedback_text']
                    ))
                conn.commit()
        except Exception as e:
            st.error(f"Error saving feedback: {str(e)}")

    def render_chat_message(self, role: str, content: str):
        """Render a chat message with feedback for assistant messages."""
        with st.chat_message(role):
            st.markdown(content)
            
            # Only show feedback if it's an assistant message AND not the welcome message
            if role == "assistant" and content != st.session_state.chat_history[0]["content"]:
                message_hash = hash(content)
                
                if message_hash not in st.session_state.submitted_feedbacks:
                    feedback_key = f"feedback_{message_hash}"
                    
                    feedback = st.feedback(
                        options="faces",
                        key=feedback_key
                    )
                    feedback_text = st.text_area(
                        "Additional comments (optional):",
                        key=f"{feedback_key}_text"
                    )
                    
                    if st.button("Send", key=f"{feedback_key}_save"):
                        if feedback is None:
                            st.error("Please provide a rating before submitting! 🙏")
                        elif not feedback_text.strip():
                            st.error("Please provide some feedback text before submitting! 💬")
                        else:
                            # Format entire chat history
                            chat_history_text = "\n\n".join([
                                f"{msg['role'].upper()}: {msg['content']}" 
                                for msg in st.session_state.chat_history
                            ])
                            
                            # Save feedback with user information
                            feedback_data = pd.DataFrame([{
                                'timestamp': pd.Timestamp.now(),
                                'user_id': st.session_state.user_id,
                                'chat_history': chat_history_text,
                                'user_input': st.session_state.chat_history[-2]['content'],
                                'agent_response': content,
                                'rating': feedback,
                                'feedback_text': feedback_text
                            }])
                            self.save_feedback(feedback_data.iloc[0].to_dict())
                            st.session_state.submitted_feedbacks.add(message_hash)
                            if 'show_toast' not in st.session_state:
                                st.session_state.show_toast = True
                            st.rerun()
            
        if hasattr(st.session_state, 'show_toast'):
            st.toast("Thank you for your feedback! 🤗", icon="✨")
            del st.session_state.show_toast
    
    def display_chat_history(self):
        """Display the chat history."""
        for message in st.session_state.chat_history:
            self.render_chat_message(message["role"], message["content"])
            
    async def process_input(self, user_input: str, pdf_text: str = None) -> str:
        """Process user input and get agent response."""
        try:
            if pdf_text:
                response = await st.session_state.agent.process(user_input, resume_content=pdf_text)
            else:
                response = await st.session_state.agent.process(user_input)
                
            if isinstance(response, dict):
                return response.get('output', str(response))
            return str(response)
        except Exception as e:
            error_message = f"Error processing your request: {str(e)}"
            st.error(error_message)
            return error_message
    
    def format_action_history(self) -> str:
        """Format the action history for display."""
        if not st.session_state.agent.action_history:
            return "No actions recorded yet"
        
        formatted_entries = []
        for entry in reversed(st.session_state.agent.action_history):  # Most recent first
            formatted_entry = (
                f"🔧 Tool: {entry['tool_name']}\n"
                f"📝 Input: {entry['tool_input']}\n"
                f"⏰ {entry['timestamp']}\n"
            )
            formatted_entries.append(formatted_entry)
        
        return formatted_entries
    
    def run(self):
        """Run the Streamlit application."""
        st.set_page_config(
            page_title="RecruiTree",
            page_icon="🌲",
            layout="wide",
        )
        
        # Add CSS to hide the sidebar
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    display: none;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Add navigation menu
        selected = option_menu(
            menu_title=None,
            options=["Chat", "Feedback Analytics"],
            icons=["chat-dots", "graph-up"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
        )
        
        if selected == "Chat":
            # Two-column layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.title("🌲 RecruiTree")
            
            with col2:
                st.header("Tools & Examples")
                
                # Add file uploader in the tools section with limit of 1 file and 2MB size
                uploaded_file = st.file_uploader("Upload your resume (PDF)", type=['pdf'], accept_multiple_files=False)
                if uploaded_file:
                    if uploaded_file.size > 2*1024*1024:
                        st.error("File size limit is 2MB")
                    else:
                        st.session_state.uploaded_resume = uploaded_file
                        st.success("Resume uploaded successfully!")
                
                with st.expander("Example Prompts", expanded=True):
                    st.markdown("""
                    Try these prompts after uploading your resume:
                    - "Create a nice personal website"
                    - "Help me improve my GitHub profile"
                    - "Create a nice Github README for my profile"
                    """)

                with st.expander("Available Tools", expanded=False):
                    st.markdown("""
                    1. **Website Generator** 📝
                        - Upload your PDF resume to get started 
                        - Creates professional website content from resume
                        - Tailor the website to your needs
                    
                    2. **Profile Optimizer** 🔍
                        - Create a GitHub README
                        - Optimize your GitHub profile
                    """)

                # Action History Panel
                with st.expander("📋 Action History", expanded=False):
                    action_history = self.format_action_history()
                    if action_history == "No actions recorded yet":
                        st.markdown("*No actions recorded yet* ⏱️")
                    elif isinstance(action_history, list):
                        for entry in action_history:
                            st.markdown(f"```\n{entry}\n```")   
                
                if st.button("Clear Chat History", type="secondary"):
                    st.session_state.chat_history = []
                    st.session_state.agent.action_history = []
                    st.rerun()

            with col1:
                # Chat interface
                self.display_chat_history()
                
                # User input
                if user_input := st.chat_input("Type your message here...", key="user_input"):
                    # Add user message to chat
                    self.render_chat_message("user", user_input)
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    # Process input with loading indicator
                    with st.spinner("Thinking..."):
                        # If resume is uploaded and user wants website content
                        if st.session_state.uploaded_resume:
                            pdf_text = get_pdf_text(st.session_state.uploaded_resume)
                            response = asyncio.run(self.process_input(user_input, pdf_text))
                        else:
                            response = asyncio.run(self.process_input(user_input))
                    
                    # Add assistant response to chat
                    self.render_chat_message("assistant", response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                    # Rerun to update the UI
                    st.rerun()

        elif selected == "Feedback Analytics":
            # Import and run the feedback analytics page
            from pages.feedback_analytics import main as feedback_main
            feedback_main()

    @staticmethod
    def generate_user_id() -> str:
        """Generate a unique user ID for the session."""
        return str(uuid.uuid4())

if __name__ == "__main__":
    app = StreamlitUI()
    app.run()
