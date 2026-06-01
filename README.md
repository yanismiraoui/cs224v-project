# RecruiTree: Automating Websites, Profiles, and Career Materials

An intelligent AI assistant that helps creating websites, profiles, and career materials using LangChain and Together AI. This project aims to streamline the job application process by providing automated tools for website creation, profile optimization, and professional content generation. Make your job application stand out with RecruiTree! 🌲

## Overview

This project implements a conversational LLM agent that assists users with:
- Creating personalized professional websites
- Enhancing GitHub presence
- Generating tailored job application materials (GitHub README, LinkedIn profile, etc.)

## Features

🌐 **Website Generation**
- Automated personal website creation
- Content customization based on user data
- Professional template suggestions

📊 **GitHub Profile Enhancement**
- README creation and improvements
- Visibility recommendations
- Suggestions to improve GitHub profile

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

3. Configure credentials. Prefer environment variables for deployment/CI:
```bash
export TOGETHER_API_KEY="your-together-api-key"
# Optional: enables feedback collection in the Streamlit app
export POSTGRES_DB="postgresql://user:password@host:5432/database"
```

For local development, you can alternatively create a root-level `secrets.toml`:
```toml
TOGETHER_API_KEY = "your-together-api-key"
POSTGRES_DB = "postgresql://user:password@host:5432/database" # optional
```

4. Run the tests:
```bash
python -m pytest -q
```

5. Run the Streamlit app:
```bash
streamlit run langchain_agents/streamlit_app.py
```

5. Enjoy!

(Optional) You can also run an example usage of the agent:
```bash
python langchain_agents/example_usage.py
```
