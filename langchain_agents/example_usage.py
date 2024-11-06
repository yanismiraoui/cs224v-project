import asyncio
from agent import JobApplicationAgent
import toml
import os
import PyPDF2

async def main():
    # Initialize agent with API key from secrets
    agent = JobApplicationAgent()
    
    # Example: Generate website content
    # website_query = """
    # I need help creating a personal website. Here's my information:
    # {
    #     "name": "John Doe",
    #     "title": "Software Engineer",
    #     "experience": ["Company A - Senior Dev", "Company B - Junior Dev"],
    #     "education": ["MS Computer Science", "BS Software Engineering"],
    #     "skills": ["Python", "JavaScript", "Cloud Computing"]
    # }
    # """
    
    # response = await agent.process(website_query)
    # print("Website Generation Response:", response)

    agent = JobApplicationAgent()
    # Using resume in cv_examples/*.pdf
    def get_pdf_text(pdf_path: str) -> str:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text

    # In the main function, replace the resume handling part:
    resume_path = './cv_examples/CV Yanis MIRAOUI.pdf'
    resume_text = get_pdf_text(resume_path)
    response = await agent.process("Create a professional website", resume_content=resume_text)
    print("Website Generation Response:", response)

    # agent = JobApplicationAgent()
    # # Example: Optimize LinkedIn profile
    # linkedin_query = """
    # Please optimize my LinkedIn profile:
    # {
    #     "headline": "Software Engineer",
    #     "about": "5 years of experience in web development",
    #     "experience": ["Full Stack Developer at Tech Corp"],
    #     "skills": ["React", "Node.js", "Python"]
    # }
    # """
    
    # response = await agent.process(linkedin_query)
    # print("LinkedIn Optimization Response:", response)

if __name__ == "__main__":
    asyncio.run(main())
