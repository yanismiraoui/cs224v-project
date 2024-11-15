from langchain.tools import tool
from typing import Optional
from custom_together_llm import TogetherLLM
from github import Github
from pydantic import BaseModel, Field
import requests
import json
from bs4 import BeautifulSoup

def parse_resume(resume_content: str, llm: Optional[object] = None) -> str:
    """
    Parse resume content into a structured JSON format.
    """
    parse_prompt = """You are a resume parser. Extract the following information in a structured format:
    1. Full Name
    2. Work Experience (including position, company, dates, and quantified achievements)
    3. Skills (both technical and soft skills)
    4. Education (including degree, school, and dates)
    5. Personal Projects (if any)
    6. Awards and Honors (if any)
    7. Publications (if any)
    8. Languages (if any)

    Output ONLY in JSON format. Do not include any comments or explanations:
    {
        "name": "string",
        "experience": [
            {
                "position": "string",
                "company": "string",
                "dates": "string",
                "achievements": ["string"]
                ...
            }
        ],
        "skills": ["string"]
    }
    However if the resume is not provided or you think it does not contain enough information return in JSON format:
    {
        "ERROR": "NOT ENOUGH INFORMATION",
        "information_needed": "..."
    }
    """
    
    return llm.invoke([
        {"role": "system", "content": parse_prompt},
        {"role": "user", "content": f"Parse this resume:\n\n{resume_content}"}
    ]).replace("```json", "").replace("```", "")

def get_github_profile(url: str, llm: Optional[object] = None) -> str:
    """
    Get GitHub profile content and parse it into a structured JSON format.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find('div', class_='application-main')

    return llm.invoke([
        {"role": "system", "content": "You are a GitHub profile parser. Extract the following information in a structured format: "},
        {"role": "user", "content": f"Parse this GitHub profile into an organized JSON format:\n\n{content}"}
    ])

# Define input schemas for tools
class WebsiteContentInput(BaseModel):
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    query: Optional[str] = Field(None, description="Optional description or additional specific instructions for content generation")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")

class ProfileOptimizerInput(BaseModel): 
    url: str = Field(description="The profile URL to optimize")
    profile_type: str = Field(description="The type of profile (linkedin/github)")
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")

@tool(args_schema=WebsiteContentInput)
def generate_website_content(query: Optional[str] = None, resume_content: Optional[str] = None, llm: Optional[TogetherLLM] = None) -> str:
    """
    Generate professional website content by analyzing a resume text content.
    If you are not provided with a resume text content, you can provide a description or additional instructions for content generation.
    The content will include sections for professional summary, experience with quantified achievements, and skills.

    Args:
        query: Optional description or additional instructions for content generation
        resume_content: Optional string containing resume text content
        llm: Optional LLM instance to use (will create new one if not provided)

    Returns:
        str: Generated website content using HTML, JavaScript and CSS
    """
    # Initialize LLM with conservative temperature for reliable output
    llm = llm or TogetherLLM(temperature=0.1)

    # Parse resume if provided
    parsed_resume = None
    if isinstance(resume_content, str):
        parsed_resume = parse_resume(resume_content, llm)
        if json.loads(parsed_resume).get("ERROR") == "NOT ENOUGH INFORMATION":
            return "Not enough information to generate website content. Please provide the following information: " + json.loads(parsed_resume)["information_needed"]

    # Generate website content
    try:
        content_prompt = """Create a professional website content in JavaScript, HTML and CSS using the provided resume data. 
        Take your time and make sure to include all the information you have. You can create as many pages as you want.
        Make sure to have a very nice design and layout that is easy to read and is visually appealing.
        Include as many as possible nice animations and transitions if you can but make sure they show up on all devices properly.
        Make sure to include these sections but also add any additional information you think is relevant:

        # Professional Summary
        Write a compelling first-person introduction highlighting key strengths and career focus.

        # Experience
        For each role, include:
        - Position and company
        - Dates
        - 3-4 quantified achievements or key responsibilities

        # Skills & Expertise
        Group skills by category (e.g., Technical, Leadership, Industry Knowledge)

        Style guidelines:
        - Use first-person perspective
        - Focus on measurable achievements
        - Keep tone professional but engaging
        - Include specific numbers and metrics where available
        - Make it look colorful and up to date
        - Make sure the title is the name of the person
        - Make sure the website does not have any layout issues

        Remember a colorful and modern design is very important. 
        This should not be a template website, it should be original and unique to you and the user do not need to modify it for it to be fully functional.
        Make sure the website is original and not copy-pasted from other websites. BE CREATIVE.
        Also, make sure all the data is present in the website, the user should not need to add any additional data by themselves.
        """
        if parsed_resume:
            return llm.invoke([
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Generate content using this resume data and these very important additional instructions: {query}\n\nResume data:\n{parsed_resume}"}
            ])
        elif query:
            return llm.invoke([
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Generate content using these very important additional instructions: {query}"}
            ])
        else:
            return """Please provide at least the following information to generate website content:
            1. Your full name
            2. Professional summary
            3. Work experience (including company names, positions, dates, and key achievements)
            4. Skills (both technical and soft skills)
            
            You can also upload a resume PDF for automatic processing."""
            
    except Exception as e:
        return f"Error processing request: {str(e)}"

@tool(args_schema=ProfileOptimizerInput)
def optimize_profile(url: str, profile_type: str, resume_content: Optional[str] = None, llm: Optional[object] = None) -> str:
    """Optimize professional profiles (LinkedIn/GitHub).
    
    Args:
        url: The profile URL to optimize
        profile_type: The type of profile (linkedin/github)
        resume_content: Optional string containing resume text content
        llm: Optional LLM instance to use (will create new one if not provided)

    Returns:
        str: Optimized profile content
    """
    if profile_type.lower() not in ['linkedin', 'github']:
        return "Error: Profile type must be either 'LinkedIn' or 'GitHub'"
    
    content = None
    if profile_type.lower() == 'linkedin':
        content = ""
    elif profile_type.lower() == 'github':
        content = get_github_profile(url, llm)
        
    parsed_resume = None
    if isinstance(resume_content, str):
        parsed_resume = parse_resume(resume_content, llm)
        if json.loads(parsed_resume).get("ERROR") == "NOT ENOUGH INFORMATION":
            return "Not enough information to optimize profile. Please provide the following information: " + json.loads(parsed_resume)["information_needed"]

    if parsed_resume:
        system_prompt = f"""You are an expert profile optimizer.
        You are given a resume and a profile URL from a {profile_type} profile.
        You need to optimize the profile based on the resume data and the profile content.
        Make sure to include all the information you have and be creative and critical.
        Remember to make optimize it for {profile_type}.
        """
        return llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Optimize this {profile_type} profile:\n{content}\n\nResume data:\n{parsed_resume}"}
        ])
    else:
        return llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Optimize this {profile_type} profile: {content}"}
        ])

@tool
def publish_to_github_pages(github_token: str, repo_name: str, description: str, html_content: Optional[str] = None, css_content: Optional[str] = None, javascript_content: Optional[str] = None, llm: Optional[object] = None) -> str:
    """
    Publishes website content to GitHub Pages

    Args:
        github_token: GitHub personal access token
        repo_name: Name for the repository (e.g., 'me', 'home', 'portfolio')
        description: Description for the repository
        html_content: Optional HTML content to publish
        css_content: Optional CSS content to publish
        javascript_content: Optional JavaScript content to publish
        llm: Optional LLM instance to use (will create new one if not provided)
    """
    llm = llm or TogetherLLM(temperature=0.1)
    
    try:
        # Initialize GitHub client
        g = Github(github_token)
        user = g.get_user()
        
        # Create or get repository
        try:
            repo = user.get_repo(repo_name)
        except:
            repo = user.create_repo(
                repo_name,
                description=description,
                homepage=f"https://{user.login}.github.io/{repo_name}",
                has_pages=True
            )
        
        # Create/update index.html
        try:
            contents = repo.get_contents("index.html")
            repo.update_file(
                contents.path,
                "Update portfolio website",
                html_content,
                contents.sha
            )
        except:
            repo.create_file(
                "index.html",
                "Initial portfolio website",
                html_content
            )
        
        # create/update the style.css file
        try:
            contents = repo.get_contents("style.css")
            repo.update_file(
                contents.path,
                "Update portfolio website",
                css_content,
                contents.sha
            )
        except:
            repo.create_file(
                "style.css",
                "Initial portfolio website",
                css_content
            )

        # create/update the script.js file
        try:
            contents = repo.get_contents("script.js")
            repo.update_file(
                contents.path,
                "Update portfolio website",
                javascript_content,
                contents.sha
            )
        except:
            repo.create_file(
                "script.js",
                "Initial portfolio website",
                javascript_content
            )
        
        # Enable GitHub Pages if not already enabled
        repo.enable_pages(source="main", path="/")
        
        return f"Website published at: https://{user.login}.github.io/{repo_name}"
    
    except Exception as e:
        return f"Error publishing website: {str(e)}"

