from langchain.tools import tool, BaseTool
from typing import Optional, Union, BinaryIO
from pypdf import PdfReader
from langchain.prompts import ChatPromptTemplate
from custom_together_llm import TogetherLLM
from pydantic import Field
import PyPDF2
from github import Github


class WebsiteContentTool(BaseTool):
    """Tool that generates website content from a resume or text description."""
    name: str = Field(default="generate_website_content")
    description: str = Field(default="""Generate professional website content by analyzing a resume PDF if provided, 
    or based on the description given. The content will include sections for professional summary, 
    experience with quantified achievements, and skills.""")
    resume_content: Optional[str] = Field(default=None)
    llm: Optional[TogetherLLM] = Field(default=None)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.llm = TogetherLLM(temperature=0.1)
    
    def set_resume(self, resume_pdf: BinaryIO) -> None:
        """Process, parse, and store structured resume content."""
        try:
            # First extract text from PDF
            pdf_reader = PyPDF2.PdfReader(resume_pdf)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            
            # Parse the text using the structured format
            parse_prompt = """You are a resume parser. Extract the following information in a structured format:
            1. Full Name
            2. Work Experience (including position, company, dates, and quantified achievements)
            3. Skills (both technical and soft skills)
            
            Format the output as JSON with the following structure:
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
            }"""
            
            messages = [
                {"role": "system", "content": parse_prompt},
                {"role": "user", "content": f"Parse this resume:\n\n{text_content}"}
            ]
            self.resume_content = self.llm.invoke(messages)
            print(self.resume_content)
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            self.resume_content = None
    
    def _run(self, query: str) -> str:
        """Generate website content based on the query and resume if available."""
        try:
            if self.resume_content:
                messages = [
                    {
                        "role": "system",
                        "content": """You are a professional website content writer. Your task is to directly write the website content, not to describe what you will do. 
                        Use the provided JSON resume data to create content with these sections:
                        
                        # Professional Summary
                        [Write a compelling introduction]
                        
                        # Experience
                        [Detail each role with company, dates, and achievements]
                        
                        # Skills & Expertise
                        [List all relevant skills]
                        
                        Write in first person, using a confident, professional tone. Focus on quantifiable achievements."""
                    },
                    {
                        "role": "user",
                        "content": f"Write the website content using this resume data:\n{self.resume_content}"
                    }
                ]
                
                website_content = self.llm.invoke(messages)
                return website_content
            else:
                return """Please provide the following information to generate website content:
                1. Your full name
                2. Professional summary
                3. Work experience (including company names, positions, dates, and key achievements)
                4. Skills (both technical and soft skills)
                
                You can also upload a resume PDF for automatic processing."""
                
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async version of _run"""
        return self._run(query)

class ProfileOptimizerTool(BaseTool):
    """Tool that optimizes professional profiles."""
    name: str = Field(default="optimize_profile")
    description: str = Field(default="Optimize professional profiles (LinkedIn/GitHub)")
    resume_content: Optional[str] = Field(default=None)

    def __init__(self, **data):
        super().__init__(**data)
    
    def set_resume(self, resume_pdf: BinaryIO) -> None:
        """Process and store resume PDF content."""
        try:
            pdf_reader = PyPDF2.PdfReader(resume_pdf)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            self.resume_content = text_content
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            self.resume_content = None
    
    def _run(self, url: str, profile_type: str) -> str:
        """Optimize professional profiles.
        
        Args:
            url: The profile URL to optimize
            profile_type: The type of profile (linkedin/github)
        """
        return f"Profile optimized for {url} of type {profile_type}"
    
    async def _arun(self, url: str, profile_type: str) -> str:
        """Async version of _run"""
        return self._run(url, profile_type)


@tool
def publish_to_github_pages(content: str, github_token: str, repo_name: str, description: str) -> str:
    """
    Publishes website content to GitHub Pages
    Args:
        content: HTML content to publish
        github_token: GitHub personal access token
        repo_name: Name for the repository (e.g., 'me', 'home', 'portfolio')
        description: Description for the repository
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
                content,
                contents.sha
            )
        except:
            repo.create_file(
                "index.html",
                "Initial portfolio website",
                content
            )
            
        # Enable GitHub Pages if not already enabled
        repo.enable_pages(source="main", path="/")
        
        return f"Website published at: https://{user.login}.github.io/{repo_name}"
    
    except Exception as e:
        return f"Error publishing website: {str(e)}"
