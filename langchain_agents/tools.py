from langchain.tools import tool
from typing import Optional
from custom_together_llm import TogetherLLM
import PyPDF2
from github import Github
from pydantic import BaseModel, Field
import json

# Define input schemas for tools
class WebsiteContentInput(BaseModel):
    query: Optional[str] = Field(None, description="Optional description or additional instructions for content generation")
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")

class ProfileOptimizerInput(BaseModel):
    url: str = Field(description="The profile URL to optimize")
    profile_type: str = Field(description="The type of profile (linkedin/github)")
    resume_content: Optional[str] = Field(None, description="Optional resume text content")

@tool(args_schema=WebsiteContentInput)
def generate_website_content(query: Optional[str] = None, resume_content: Optional[str] = None, llm: Optional[TogetherLLM] = None) -> str:
    """Generate professional website content by analyzing a resume PDF if provided, 
    or based on the description given. The content will include sections for professional summary, 
    experience with quantified achievements, and skills.
    
    Args:
        query: Optional description or additional instructions for content generation
        resume_content: Optional string containing resume text content
        llm: Optional LLM instance to use (will create new one if not provided)

    Returns:
        str: Generated website content
    """
    # Initialize LLM with conservative temperature for reliable output
    llm = llm or TogetherLLM(temperature=0.1)

    # Parse resume if provided
    parsed_resume = None
    if isinstance(resume_content, str):
        try:
            parse_prompt = """You are a resume parser. Extract the following information in a structured format:
            1. Full Name
            2. Work Experience (including position, company, dates, and quantified achievements)
            3. Skills (both technical and soft skills)
            4. Education (including degree, school, and dates)

            Output JSON format:
            {
                "name": "string",
                "experience": [
                    {
                        "position": "string",
                        "company": "string",
                        "dates": "string",
                        "achievements": ["string"]
                    }
                ],
                "skills": ["string"]
            }
            However if the resume is not provided or does not contain enough information return in JSON format:
            {
               "ERROR": "NOT ENOUGH INFORMATION",
               "information_needed": "string"
            }
            """
            
            parsed_resume = llm.invoke([
                {"role": "system", "content": parse_prompt},
                {"role": "user", "content": f"Parse this resume:\n\n{resume_content}"}
            ])
            if json.loads(parsed_resume).get("ERROR") == "NOT ENOUGH INFORMATION":
                return "Not enough information to generate website content. Please provide the following information: " + json.loads(parsed_resume)["information_needed"]
            
        except Exception as e:
            print(f"Resume parsing failed: {str(e)}")
            return "Error: Unable to parse resume content. Please check the format and try again."

    # Generate website content
    try:
        if parsed_resume:
            content_prompt = """Create professional website content in JavaScript, HTML and CSS using the provided resume data. 
            Take your time and make sure to include all the information you have. You can create as many pages as you want.
            Make sure to have a very nice design and layout that is easy to read and is visually appealing.
            Include as many as possible nice animations and transitions if you can.
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
            - Make it look modern, colorful and up to date
            - Make sure the title is the name of the person
            - Make sure the website does not have any layout issues

            Remember a very sleek and modern design is very important. 
            Make sure the website is original and not copy-pasted from other websites. BE CREATIVE.
            """

            return llm.invoke([
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Generate content using this resume data and these very important additional instructions: {query}\n\nResume data:\n{parsed_resume}"}
            ])
        else:
            return """Please provide the following information to generate website content:
            1. Your full name
            2. Professional summary
            3. Work experience (including company names, positions, dates, and key achievements)
            4. Skills (both technical and soft skills)
            
            You can also upload a resume PDF for automatic processing."""
            
    except Exception as e:
        return f"Error processing request: {str(e)}"

@tool
def optimize_profile(url: str, profile_type: str, resume_content: Optional[str] = None) -> str:
    """Optimize professional profiles (LinkedIn/GitHub).
    
    Args:
        url: The profile URL to optimize
        profile_type: The type of profile (linkedin/github)
        resume_content: Optional string containing resume text content

    Returns:
        str: Optimized profile content
    """
    if profile_type.lower() not in ['linkedin', 'github']:
        return "Error: Profile type must be either 'LinkedIn' or 'GitHub'"
        
    if resume_content:
        try:
            pdf_reader = PyPDF2.PdfReader(resume_content)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            resume_content = text_content
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
    else:
        return "Please provide the resume content to optimize the profile."
    
    # TODO: Implement actual profile optimization logic
    return f"Profile optimized for {url} of type {profile_type}"

@tool
def publish_to_github_pages(github_token: str, repo_name: str, description: str, html_content: Optional[str] = None, css_content: Optional[str] = None) -> str:
    """
    Publishes website content to GitHub Pages
    Args:
        github_token: GitHub personal access token
        repo_name: Name for the repository (e.g., 'me', 'home', 'portfolio')
        description: Description for the repository
        html_content: Optional HTML content to publish
        css_content: Optional CSS content to publish
    """
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
        
        # Enable GitHub Pages if not already enabled
        repo.enable_pages(source="main", path="/")
        
        return f"Website published at: https://{user.login}.github.io/{repo_name}"
    
    except Exception as e:
        return f"Error publishing website: {str(e)}"

