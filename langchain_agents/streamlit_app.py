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
from PIL import Image
from streamlit.components.v1 import html
import glob
import shutil
import base64

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
        if 'profile_pic_base64' not in st.session_state:
            st.session_state.profile_pic_base64 = None
        
        # Use the connection string directly instead of separate parameters
        self.db_url = secrets['POSTGRES_DB']
        
        # Initialize database table if it doesn't exist
        self.initialize_database()
        
        # Add a new session state variable to track submitted feedback
        if 'submitted_feedbacks' not in st.session_state:
            st.session_state.submitted_feedbacks = set()
        
        # Add website files state
        if 'website_files' not in st.session_state:
            st.session_state.website_files = {}

        self.website_temp_dir = Path(__file__).parent.parent / "temp"
        self.static_folder = Path(__file__).parent / "static" / "images"
        self.static_folder.mkdir(parents=True, exist_ok=True)
    
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

    def save_profile_pic(self, uploaded_file) -> str:
        """Save profile picture to static folder and return the path."""
        try:
            # Open and process the image
            img = Image.open(uploaded_file)

            # Convert to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Resize
            max_size = (200, 200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Generate unique filename
            filename = f"profile_pic_{st.session_state.user_id}.jpg"
            filepath = self.static_folder / filename

            # Save image
            img.save(filepath, format="JPEG", quality=70, optimize=True)

            # Return relative path
            return f"static/images/{filename}"

        except Exception as e:
            st.error(f"Error saving image: {str(e)}")
            return None
    
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
        
        # Check if website files exist
        website_files = self.load_website_files()

        # Check if README exists
        readme = self.load_readme()
        
        # Create horizontal navigation menu
        menu_options = ["Chat", "Preview", "Feedback Analytics"]
        menu_icons = ["chat-dots", "globe", "graph-up"]
        
        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
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
                
                # Create two columns for the upload buttons
                upload_col1, upload_col2 = st.columns(2)

                with upload_col1:
                    # Resume uploader
                    uploaded_file = st.file_uploader("Upload Resume (PDF)", 
                                                   type=['pdf'], 
                                                   accept_multiple_files=False,
                                                   key="resume_uploader")
                    if uploaded_file:
                        if uploaded_file.size > 2*1024*1024:
                            st.error("File size limit is 2MB")
                        else:
                            st.session_state.uploaded_resume = uploaded_file
                            st.success("Resume uploaded!")

                with upload_col2:
                    # Profile picture uploader
                    uploaded_file = st.file_uploader("Upload your profile picture", type=['jpg', 'jpeg', 'png'])
                    if uploaded_file is not None:
                        # Create temp/imgs directory if it doesn't exist
                        imgs_dir = os.path.join("temp", "imgs")
                        os.makedirs(imgs_dir, exist_ok=True)  # This creates both temp and imgs directories if they don't exist

                        # Save the uploaded file
                        profile_pic = Image.open(uploaded_file)
                        profile_pic_path = os.path.join(imgs_dir, "profile_pic.jpg")

                        # Convert to RGB if necessary (in case of PNG upload)
                        if profile_pic.mode in ('RGBA', 'P'):
                            profile_pic = profile_pic.convert('RGB')

                        # Save the image
                        profile_pic.save(profile_pic_path)

                        # Show the uploaded image
                        st.image(profile_pic, caption='Uploaded Profile Picture', width=200)
                
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

        elif selected == "Preview":
            st.title("🌐 Preview")
            if not website_files and not readme:
                st.error("No website files or README found. Please generate a website or README first.")
            else:
                preview_col, explorer_col = st.columns([3, 1])
                
                with explorer_col:
                    st.subheader("📁 Files")
                    file_options = list(website_files.keys())
                    if readme:
                        file_options.append("README.md")
                    selected_file = st.radio(
                        "Select file to preview:",
                        file_options,
                        index=file_options.index('index.html') if 'index.html' in file_options else 0
                    )
                    
                    # Download button
                    if st.button("📥 Download All Files"):
                        zip_path = self.website_temp_dir / "recruitree.zip"
                        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', self.website_temp_dir)
                        
                        with open(zip_path, 'rb') as f:
                            st.download_button(
                                label="Download ZIP",
                                data=f,
                                file_name="recruitree.zip",
                                mime="application/zip"
                            )
                    
                    # Source code viewer
                    with st.expander("📝 Source Code", expanded=False):
                        st.code(
                            website_files[selected_file] if selected_file in website_files else readme,
                            language='html' if selected_file.endswith('.html') else
                                    'css' if selected_file.endswith('.css') else
                                    'javascript'
                        )
                
                with preview_col:
                    st.subheader("🖥️ Preview")
                    if selected_file.endswith('.html'):
                        # Combine HTML with CSS and JS
                        html_content = website_files[selected_file]
                        
                        # Ensure the HTML has proper head and body tags
                        if '<head>' not in html_content:
                            html_content = f"""
                            <html>
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            </head>
                            <body>
                                {html_content}
                            </body>
                            </html>
                            """
                        
                        # Insert CSS into the HTML head
                        css_content = """
                        <style>
                            {existing_css}
                            
                            /* Preview container styles */
                            .preview-container {{
                                border: 1px solid #ddd;
                                border-radius: 8px;
                                padding: 20px;
                                background: white;
                                height: 700px;
                            }}
                        </style>
                        """
                        if 'style.css' in website_files:
                            css_content = css_content.format(existing_css=website_files['style.css'])
                        else:
                            css_content = css_content.format(existing_css='')
                        
                        html_content = html_content.replace('</head>', f'{css_content}</head>')
                        
                        # Insert JS into the HTML body
                        js_content = ""
                        if 'script.js' in website_files:
                            js_content = f"<script>{website_files['script.js']}</script>"
                        html_content = html_content.replace('</body>', f'{js_content}</body>')
                        
                        # Handle profile picture
                        profile_pic_path = os.path.join(self.website_temp_dir, "imgs", "profile_pic.jpg")
                        if os.path.exists(profile_pic_path):
                            img_base64 = self.get_image_base64(profile_pic_path)
                            if img_base64:
                                html_content = html_content.replace(
                                    'src="imgs/profile_pic.jpg"',
                                    f'src="data:image/jpeg;base64,{img_base64}"'
                                )
                        
                        # Render the complete webpage
                        html(html_content, height=700, scrolling=True)
                    elif selected_file.endswith(('.png', '.jpg', '.jpeg')):
                        st.image(website_files[selected_file], caption=selected_file)
                    elif selected_file.endswith('.css'):
                        st.info("CSS files can only be viewed in the Source Code section")
                    elif selected_file.endswith('.js'):
                        st.info("JavaScript files can only be viewed in the Source Code section")
                    elif selected_file == "README.md":
                        st.markdown(readme)
            
        elif selected == "Feedback Analytics":
            # Import and run the feedback analytics page
            from pages.feedback_analytics import main as feedback_main
            feedback_main()

    @staticmethod
    def generate_user_id() -> str:
        """Generate a unique user ID for the session."""
        return str(uuid.uuid4())

    def load_website_files(self):
        """Load all website files from temp directory."""
        website_files = {}
        for file_path in glob.glob(str(self.website_temp_dir / "**/*.*"), recursive=True):
            if file_path.endswith(('.html', '.css', '.js')):
                with open(file_path, 'r', encoding='utf-8') as f:
                    relative_path = Path(file_path).relative_to(self.website_temp_dir)
                    website_files[str(relative_path)] = f.read()
            elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                website_files[str(Path(file_path).relative_to(self.website_temp_dir))] = file_path
        return website_files
    
    def load_readme(self):
        """Load the README file from temp directory."""
        readme_path = self.website_temp_dir / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def get_image_base64(self, image_path):
        """Convert image to base64 string."""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            st.error(f"Error encoding image: {str(e)}")
            return None

if __name__ == "__main__":
    app = StreamlitUI()
    app.run()
