# RecruiTree: Automating Websites, Profiles, and Career Materials

> **V2 rebuild in progress:** This repository is being rebuilt from the original Streamlit + LangChain prototype into a cleaner, evidence-first career asset system. The current V1 prototype remains available as a baseline reference; see [`docs/product/current-state.md`](docs/product/current-state.md) and [`docs/plans/2026-05-21-recruitree-rebuild.md`](docs/plans/2026-05-21-recruitree-rebuild.md).

An intelligent AI assistant that helps create websites, profiles, and career materials using LangChain and Together AI. This project aims to streamline the job application process by providing automated tools for website creation, profile optimization, and professional content generation. Make your job application stand out with RecruiTree! 🌲

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

3. Set V1 credentials in a root-level `secrets.toml` file. The legacy app expects at least:
```toml
TOGETHER_API_KEY = "..."
POSTGRES_DB = "..."
```

For more baseline details, see [`docs/product/current-state.md`](docs/product/current-state.md).

4. Run the Streamlit app:
```bash
streamlit run langchain_agents/streamlit_app.py
```

5. Enjoy!

(Optional) You can also run an example usage of the agent:
```bash
python langchain_agents/example_usage.py
```
