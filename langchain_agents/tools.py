from langchain.tools import tool
from typing import Optional
from custom_together_llm import TogetherLLM
from github import Github
from pydantic import BaseModel, Field
import requests
import json
from bs4 import BeautifulSoup
import random

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
    profile_type: str = Field(description="The type of profile (GitHub)")
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")

class HomeScreenInput(BaseModel):
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    style: Optional[str] = Field(None, description="Optional style preference")
    color_scheme: Optional[str] = Field(None, description="Optional color scheme preference")
    profile_image_url: Optional[str] = Field(None, description="URL of the profile image")
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
        # Randomly select a website style/theme
        website_styles = [
            "minimal-modern",
            "creative-portfolio",
            "tech-focused",
            "artistic-showcase",
            "professional-corporate",
            "playful-interactive"
        ]
        
        selected_style = random.choice(website_styles)
        print(f"Selected style: {selected_style}")
        
        content_prompt = f"""Create a unique and creative {selected_style} website using JavaScript, HTML and CSS. 
        Focus on making this website stand out with:

        - Unique layout arrangements (avoid traditional top-to-bottom layouts)
        - Creative navigation patterns
        - Interactive elements that engage visitors
        - Modern design elements like glassmorphism, neumorphism, or creative gradients
        - Innovative ways to present traditional content sections
        
        If the style is:
        - minimal-modern: Focus on typography and whitespace
        - creative-portfolio: Use bold color and color gradients and unusual layouts
        - tech-focused: Include terminal-like interfaces or code-inspired designs and fonts
        - artistic-showcase: Incorporate canvas animations and artistic transitions
        - professional-corporate: Elegant animations and clean design
        - playful-interactive: Add game-like elements and playful interactions

        Required sections (but this is not exhaustive):
        - Professional Summary
        - Experience
        - Skills & Expertise

        Technical requirements:
        - Ensure responsive design
        - Make it colorful and creative
        - Include modern CSS features (Grid, Flexbox, CSS Variables)
        - Add meaningful animations and transitions
        - Make it interactive and engaging
        - Ensure accessibility
        
        The website should be complete and ready to use without modifications.
        """
        llm = TogetherLLM(temperature=0.7)
        if parsed_resume:
            response = llm.invoke([
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Generate content using this resume data and these very important additional instructions: {query}\n\nResume data:\n{parsed_resume}"}
            ]).replace('"', "'")
            # Save response HTML, CSS and JS to files in temp folder
            with open(f"temp/index.html", "w") as file:
                file.write(response.split("```html")[1].split("```")[0])
            with open(f"temp/style.css", "w") as file:
                file.write(response.split("```css")[1].split("```")[0])
            with open(f"temp/script.js", "w") as file:
                file.write(response.split("```javascript")[1].split("```")[0])
            return response
        elif query:
            response = llm.invoke([
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Generate content using these very important additional instructions: {query}"}
            ]).replace('"', "'")
            # Save response HTML, CSS and JS to files in temp folder
            with open(f"temp/index.html", "w") as file:
                file.write(response.split("```html")[1].split("```")[0])
            with open(f"temp/style.css", "w") as file:
                file.write(response.split("```css")[1].split("```")[0])
            with open(f"temp/script.js", "w") as file:
                file.write(response.split("```javascript")[1].split("```")[0])
            return response
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
    """Optimize professional profiles (GitHub).
    
    Args:
        url: The profile URL to optimize
        profile_type: The type of profile (GitHub)
        resume_content: Optional string containing resume text content
        llm: Optional LLM instance to use (will create new one if not provided)

    Returns:
        str: Optimized profile content
    """
    if profile_type.lower() not in ['github']:
        return "Error: Profile type must be 'GitHub'"
    
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

# @tool(args_schema=HomeScreenInput)
# def generate_home_screen(
#     resume_content: Optional[str] = None, 
#     style: Optional[str] = None, 
#     color_scheme: Optional[str] = None,
#     profile_image_url: Optional[str] = None,
#     llm: Optional[TogetherLLM] = None
# ) -> str:
#     """Generate a minimal home screen with optional profile picture."""
    
#     llm = llm or TogetherLLM(temperature=0.7)
    
#     # Parse resume to extract only needed information
#     if isinstance(resume_content, str):
#         parsed_resume = parse_resume(resume_content, llm)
#         resume_data = json.loads(parsed_resume)
#         if resume_data.get("ERROR") == "NOT ENOUGH INFORMATION":
#             return "Not enough information. Please provide: name, current role/education, and a brief introduction."
    
#     styles = {
#         "modern-gradient": "Clean lines with gradient backgrounds and smooth transitions",
#         "minimal-elegant": "Simple, typography-focused with plenty of whitespace",
#         "artistic-abstract": "Creative, unique layouts with artistic elements",
#     }
    
#     color_schemes = {
#         "vibrant-purple-blue": "background: linear-gradient(45deg, #6366f1, #2563eb)",
#         "sunset-orange-pink": "background: linear-gradient(45deg, #f59e0b, #ec4899)",
#         "midnight-dark": "background: linear-gradient(45deg, #1e293b, #0f172a)",
#     }
    
#     selected_style = style if style in styles else random.choice(list(styles.keys()))
#     selected_colors = color_scheme if color_scheme in color_schemes else random.choice(list(color_schemes.keys()))
    
#     # Add profile image handling to the prompt
#     profile_image_css = """
#     .profile-image {
#         width: 200px;
#         height: 200px;
#         border-radius: 50%;
#         object-fit: cover;
#         margin-bottom: 2rem;
#         box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
#         border: 4px solid rgba(255, 255, 255, 0.2);
#         animation: fadeIn 1s ease-out;
#     }
#     """
    
#     home_screen_prompt = f"""Create a minimal, impactful home screen using HTML, CSS, and JavaScript.
    
#     Style Theme: {selected_style}
#     Color Scheme: {selected_colors}
    
#     IMPORTANT - Include these elements in order:
#     1. Profile Picture (circular, centered, with subtle border and shadow)
#     2. Full Name (large, prominent typography)
#     3. Current Role or Education
#     4. A brief, 1-2 sentence introduction
    
#     Use this profile image URL if provided: {profile_image_url if profile_image_url else "No image provided"}
    
#     If no image URL is provided, add a placeholder with initials.
    
#     DO NOT include:
#     - Work history
#     - Skills
#     - Projects
#     - Contact information
#     - Navigation menus
#     - Social media links
    
#     Design Requirements:
#     1. Single-page, full-screen layout
#     2. Large, creative typography for the name
#     3. Smooth entrance animations
#     4. Subtle hover effects
#     5. Clean, minimal design
#     6. Responsive layout
    
#     Technical Requirements:
#     - Modern CSS (Grid/Flexbox)
#     - Simple animations for text entrance
#     - Clean, minimal JavaScript
#     - Well-commented code
    
#     The final design should be striking yet minimal, focusing attention on these three key elements.
#     Return complete, ready-to-use HTML, CSS, and JavaScript code.
#     """
    
#     try:
#         if parsed_resume:
#             # Extract only needed information
#             name = resume_data.get("name", "")
#             current_role = ""
#             if "experience" in resume_data and resume_data["experience"]:
#                 current_role = f"{resume_data['experience'][0]['position']} at {resume_data['experience'][0]['company']}"
#             elif "education" in resume_data and resume_data["education"]:
#                 current_role = f"Student at {resume_data['education'][0]['school']}"
            
#             return llm.invoke([
#                 {"role": "system", "content": home_screen_prompt},
#                 {"role": "user", "content": f"""Generate a minimal home screen with:
#                 Name: {name}
#                 Current Role: {current_role}
#                 Create a brief, compelling introduction based on the experience."""}
#             ]).replace('"', "'")
#         else:
#             return llm.invoke([
#                 {"role": "system", "content": home_screen_prompt},
#                 {"role": "user", "content": "Generate a template home screen with placeholder content for name, role, and brief intro."}
#             ]).replace('"', "'")
            
#     except Exception as e:
#         return f"Error generating home screen: {str(e)}"

@tool
def publish_to_github_pages(github_token: str, description: str, llm: Optional[object] = None) -> str:
    """
    Publishes website content to GitHub Pages

    Args:
        github_token: GitHub personal access token (REQUIRED)
        description: Description for the repository
        llm: Optional LLM instance to use (will create new one if not provided)
    """
    llm = llm or TogetherLLM(temperature=0.1)
    
    try:
        # Load HTML, CSS and JS from temp folder
        with open(f"temp/index.html", "r") as file:
            html_content = file.read()
        with open(f"temp/style.css", "r") as file:
            css_content = file.read()
        with open(f"temp/script.js", "r") as file:
            javascript_content = file.read()
        
        # Initialize GitHub client
        g = Github(github_token)
        user = g.get_user()
        repo_name = f"{user.login}.github.io"
        
        # Create or get repository
        try:
            repo = user.get_repo(repo_name)
        except:
            repo = user.create_repo(
                repo_name,
                description=description,
                homepage=f"https://{user.login}.github.io",
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
        
        return f"Website published at: https://{user.login}.github.io"
    
    except Exception as e:
        return f"Error publishing website: {str(e)}"

