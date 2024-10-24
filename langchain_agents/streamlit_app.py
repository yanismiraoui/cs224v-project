import streamlit as st
import asyncio
import json
from agent import JobApplicationAgent
from typing import Dict

class StreamlitUI:
    def __init__(self):
        # Initialize session state
        if 'agent' not in st.session_state:
            api_key = st.secrets.get("TOGETHER_API_KEY", None)
            st.session_state.agent = JobApplicationAgent(api_key=api_key)
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
        return response
    
    def run(self):
        """Run the Streamlit application."""
        st.title("Job Application Assistant")
        
        # Sidebar for configuration
        with st.sidebar:
            st.header("Configuration")
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
            
            st.header("Tools")
            tool_option = st.selectbox(
                "Select Tool",
                ["Website Generator", "LinkedIn Optimizer", "GitHub Optimizer"]
            )
            
            # Tool-specific inputs
            if tool_option == "Website Generator":
                st.subheader("Website Information")
                name = st.text_input("Name")
                title = st.text_input("Professional Title")
                experience = st.text_area("Experience (one per line)")
                education = st.text_area("Education (one per line)")
                skills = st.text_area("Skills (one per line)")
                
                if st.button("Generate Website"):
                    user_data = {
                        "name": name,
                        "title": title,
                        "experience": experience.split("\n"),
                        "education": education.split("\n"),
                        "skills": skills.split("\n")
                    }
                    prompt = f"Generate a personal website with this information: {json.dumps(user_data)}"
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    
            elif tool_option == "LinkedIn Optimizer":
                st.subheader("LinkedIn Profile")
                headline = st.text_input("Headline")
                about = st.text_area("About")
                profile_experience = st.text_area("Experience")
                profile_skills = st.text_area("Skills")
                
                if st.button("Optimize Profile"):
                    profile_data = {
                        "headline": headline,
                        "about": about,
                        "experience": profile_experience.split("\n"),
                        "skills": profile_skills.split("\n")
                    }
                    prompt = f"Optimize this LinkedIn profile: {json.dumps(profile_data)}"
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
        
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
