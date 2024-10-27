import streamlit as st
import asyncio
from agent import JobApplicationAgent
import toml
import os

secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.streamlit', 'secrets.toml')
secrets = toml.load(secrets_path)
os.environ['TOGETHER_API_KEY'] = secrets['TOGETHER_API_KEY']

class StreamlitUI:
    def __init__(self):
        # Initialize session state
        if 'agent' not in st.session_state:
            st.session_state.agent = JobApplicationAgent()
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
    def render_chat_message(self, role: str, content: str):
        """Render a chat message with the appropriate styling."""
        with st.chat_message(role):
            st.markdown(content)
            
    def display_chat_history(self):
        """Display the chat history."""
        for message in st.session_state.chat_history:
            self.render_chat_message(message["role"], message["content"])
            
    async def process_input(self, user_input: str):
        """Process user input and get agent response."""
        response = await st.session_state.agent.process(user_input)
        print("Raw agent response:", response)
        return response.get('output', response) if isinstance(response, dict) else response
    
    def run(self):
        """Run the Streamlit application."""
        st.title("Job Application Assistant")
        
        # Sidebar for configuration
        with st.sidebar:
            st.header("Configuration")
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
            
            st.markdown("""
            ### Available Tools
            1. Website Generator - Create professional website content
            2. Profile Optimizer - Optimize LinkedIn/GitHub profiles
            
            ### Example Prompts
            - "Help me create a personal website with my experience..."
            - "Can you optimize my LinkedIn profile?"
            - "I need help improving my GitHub profile..."
            """)
        
        # Main chat interface
        st.header("Chat Interface")
        self.display_chat_history()
        
        # User input
        if user_input := st.chat_input("Type your message here..."):
            self.render_chat_message("user", user_input)
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner("Thinking..."):
                # Process the input asynchronously
                response = asyncio.run(self.process_input(user_input))
                
            self.render_chat_message("assistant", response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    app = StreamlitUI()
    app.run()
