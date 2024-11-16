# Job Application Assistant with LLM

An intelligent AI assistant that helps optimize job applications and professional profiles using LangChain and Together AI. This project aims to streamline the job application process by providing automated tools for website creation, profile optimization, and professional content generation.

## Overview

This project implements a conversational LLM agent that assists users with:
- Creating personalized professional websites
- Enhancing GitHub presence
- Generating tailored job application materials

## Features

🌐 **Website Generation**
- Automated personal website creation
- Content customization based on user data
- Professional template suggestions

📊 **GitHub Profile Enhancement**
- README creation and improvements
- Visibility recommendations

💬 **Interactive Chat Interface**
- User-friendly Streamlit UI
- Conversation memory and context
- Real-time responses
- Feedback tracking and analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yanismiraoui/cs224v-project.git
```

2. Install the dependencies (recommended to use a virtual environment):
```bash
pip install -r requirements.txt
```

3. Set your Together API key in a `secrets.toml` file.

4. Run the Streamlit app:
```bash
streamlit run langchain_agents/streamlit_app.py
```

5. Enjoy!

(Optional) You can also run an example usage of the agent:
```bash
python langchain_agents/example_usage.py
```