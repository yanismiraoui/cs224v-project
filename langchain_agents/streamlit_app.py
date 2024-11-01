import streamlit as st
import asyncio
from agent import JobApplicationAgent
import toml
import os
from typing import Union, BinaryIO
import io

# Initialize environment variables and configurations
try:
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secrets.toml')
    secrets = toml.load(secrets_path)
    os.environ['TOGETHER_API_KEY'] = secrets['TOGETHER_API_KEY']
except Exception as e:
    st.error(f"Error loading secrets: {str(e)}")
    st.stop()

class StreamlitUI:
    def __init__(self):
        # Initialize session state
        if 'agent' not in st.session_state:
            st.session_state.agent = asyncio.run(self.initialize_agent())
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        # Add file upload state
        if 'uploaded_resume' not in st.session_state:
            st.session_state.uploaded_resume = None
    
    @staticmethod
    async def initialize_agent() -> JobApplicationAgent:
        """Initialize the agent asynchronously."""
        return JobApplicationAgent()
            
    def render_chat_message(self, role: str, content: str):
        """Render a chat message with the appropriate styling."""
        with st.chat_message(role):
            st.markdown(content)
            
    def display_chat_history(self):
        """Display the chat history."""
        for message in st.session_state.chat_history:
            self.render_chat_message(message["role"], message["content"])
            
    async def process_input(self, user_input: str, pdf_file: BinaryIO = None) -> str:
        """Process user input and get agent response."""
        try:
            if pdf_file:
                response = await st.session_state.agent.process(user_input, resume_pdf=pdf_file)
            else:
                response = await st.session_state.agent.process(user_input)
                
            if isinstance(response, dict):
                return response.get('output', str(response))
            return str(response)
        except Exception as e:
            error_message = f"Error processing your request: {str(e)}"
            st.error(error_message)
            return error_message
    
    def run(self):
        """Run the Streamlit application."""
        st.set_page_config(
            page_title="Job Application Assistant",
            page_icon="💼",
            layout="wide"
        )
        
        # Main layout
        st.title("💼 Job Application Assistant")
        
        # Two-column layout
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.header("Tools & Examples")
            
            # Add file uploader in the tools section
            uploaded_file = st.file_uploader("Upload your resume (PDF)", type=['pdf'])
            if uploaded_file:
                st.session_state.uploaded_resume = uploaded_file
                st.success("Resume uploaded successfully!")
            
            with st.expander("Available Tools", expanded=True):
                st.markdown("""
                1. **Website Generator** 📝
                   - Creates professional website content from resume
                   - Upload your PDF resume to get started
                
                2. **Profile Optimizer** 🔍
                   - LinkedIn profile optimization
                   - GitHub profile enhancement
                """)
            
            with st.expander("Example Prompts", expanded=True):
                st.markdown("""
                Try these prompts:
                - "Create a personal website showcasing my experience as a software engineer with 5 years of experience in Python and JavaScript"
                - "Optimize my LinkedIn profile: [URL]"
                - "Help improve my GitHub profile at [username]"
                """)
            
            if st.button("Clear Chat History", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col1:
            # Chat interface
            st.header("Chat Interface")
            self.display_chat_history()
            
            # User input
            if user_input := st.chat_input("Type your message here...", key="user_input"):
                # Add user message to chat
                self.render_chat_message("user", user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Process input with loading indicator
                with st.spinner("Processing your request..."):
                    # If resume is uploaded and user wants website content
                    if st.session_state.uploaded_resume and "website" in user_input.lower():
                        # Reset file pointer to beginning
                        st.session_state.uploaded_resume.seek(0)
                        # Convert to BytesIO
                        pdf_bytes = io.BytesIO(st.session_state.uploaded_resume.read())
                        # Add file context to the request
                        enhanced_input = f"Using the uploaded resume, {user_input}"
                        response = asyncio.run(self.process_input(enhanced_input, pdf_bytes))
                    else:
                        response = asyncio.run(self.process_input(user_input))
                
                # Add assistant response to chat
                self.render_chat_message("assistant", response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                # Rerun to update the UI
                st.rerun()

if __name__ == "__main__":
    app = StreamlitUI()
    app.run()
