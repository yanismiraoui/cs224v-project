import asyncio
from agent import JobApplicationAgent
import toml
import os

async def main():
    # Initialize agent with API key from secrets
    agent = JobApplicationAgent()
    
    # Example: Generate website content
    website_query = """
    I need help creating a personal website. Here's my information:
    {
        "name": "John Doe",
        "title": "Software Engineer",
        "experience": ["Company A - Senior Dev", "Company B - Junior Dev"],
        "education": ["MS Computer Science", "BS Software Engineering"],
        "skills": ["Python", "JavaScript", "Cloud Computing"]
    }
    """
    
    response = await agent.process(website_query)
    print("Website Generation Response:", response)
    

    agent = JobApplicationAgent()
    # Example: Optimize LinkedIn profile
    linkedin_query = """
    Please optimize my LinkedIn profile:
    {
        "headline": "Software Engineer",
        "about": "5 years of experience in web development",
        "experience": ["Full Stack Developer at Tech Corp"],
        "skills": ["React", "Node.js", "Python"]
    }
    """
    
    response = await agent.process(linkedin_query)
    print("LinkedIn Optimization Response:", response)

if __name__ == "__main__":
    asyncio.run(main())
