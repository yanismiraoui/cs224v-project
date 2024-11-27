from langchain.tools import tool
from typing import Optional, Dict
from custom_together_llm import TogetherLLM
from github import Github
from pydantic import BaseModel, Field
import requests
import json
from bs4 import BeautifulSoup
import random
from agents.home_screen_generator import HomeScreenGenerator
import os
from agents.page_router import get_router, PageRouter

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
    content = soup.find('article', class_='markdown-body entry-content container-lg f5')

    return llm.invoke([
        {"role": "system", "content": "You are a HTML GitHub profile parser. You have to extract the information from the HTML content and return it in a structured JSON format. Make sure to include ALL the information you can find in the HTML content. ONLY return the JSON, nothing else."},
        {"role": "user", "content": f"Parse this GitHub profile into an organized JSON format:\n\n{content}"}
    ])

# Define input schemas for tools
class WebsiteContentInput(BaseModel):
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    query: Optional[str] = Field(None, description="Optional description or additional specific instructions for content generation")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")

class ProfileOptimizerInput(BaseModel): 
    url: str = Field(description="The profile URL to optimize")
    resume_content: Optional[str] = Field(None, description="Optional resume text content")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")

class GitHubReadmeInput(BaseModel):
    query: Optional[str] = Field(None, description="Optional description or additional specific instructions for content generation")
    resume_content: str = Field(description="Resume text content")
    github_token: str = Field(description="GitHub personal access token")
    llm: Optional[object] = Field(None, description="Optional LLM instance to use")


home_screen_agent = HomeScreenGenerator()
@tool
async def generate_home_screen(
    user_input: str,
    resume_content: Optional[str] = None,
    llm: Optional[object] = None
) -> Dict[str, str]:
    """
    ONLY use this tool to create or modify the HOME/LANDING PAGE of a personal website.
    This tool specifically handles the main entry point of the website.
    
    Examples of when to use this tool:
    - "Create a landing page for my website"
    - "Design the home page of my portfolio"
    - "Update the main page of my site"
    - "Make my home page more modern"
    
    Do NOT use this tool for:
    - Other website pages (projects, contact, about, etc.)
    - Full website generation
    - GitHub profile changes
    - README generation
    
    Args:
        user_input: The user's request for home page creation or modification
        resume_content: Optional resume text to use for content
        llm: Optional LLM instance
    """
    return await home_screen_agent.generate_home_screen(
        user_input=user_input,
        resume_content=resume_content,
    )

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

@tool(args_schema=GitHubReadmeInput)
def generate_github_readme(query: Optional[str] = None, resume_content: str = None, github_token: str = None, llm: Optional[object] = None) -> str:
    """Generate a GitHub README file based on resume content.
    If you are not provided with a resume text content, you can provide a description or additional instructions for content generation.

    Args:
        query: Optional description or additional instructions for content generation
        resume_content: String containing resume text content
        github_token: GitHub personal access token
        llm: Optional LLM instance to use (will create new one if not provided)
    """
    llm = llm or TogetherLLM(temperature=0.7)
    try:
        g = Github(github_token)
        user = g.get_user()
        username = user.login
    except Exception as e:
        username = None
    
    if not resume_content:
        return f"""If not a complete resume, please provide at least the following information to generate a GitHub README file:
        1. Your full name
        2. Professional summary
        3. Work experience (including company names, positions, dates, and key achievements)
        4. Skills (both technical and soft skills)"""

    content_prompt = """
    You are a GitHub README generator. Generate a README file based on the resume content.
    It should be fun and creative.
    Here is an example of a good README structure, feel free to use it and modify it:
    ```
    <img src="https://komarev.com/ghpvc/?username=[USERNAME]&style=flat-square">
    # Hi everyone :wave:

    I'm a [JOB] from [LOCATION], [BIO].

    ## Quick overview


    #### GitHub stats 
    <a href="https://github.com/[USERNAME]/github-readme-stats">
    <img align="center" src="https://github-readme-stats.anuraghazra1.vercel.app/api?username=[USERNAME]&show_icons=true&line_height=27&include_all_commits=true" alt="My github stats" />
    </a>

    #### GitHub Streaks
    <a href="https://streak-stats.demolab.com/?user=[USERNAME]">
    <img align="center" src="https://streak-stats.demolab.com/?user=[USERNAME]" alt="My github streak" />
    </a>

    ### Current Projects

    [PROJECTS]

    ## My skills 📜

    ### Web technologies

    - Python 
    - C++
    - JavaScript
    - TypeScript
    - Next.js
    ...

    ### Languages 🌐

    | Language      | Proficiency                                                               |
    | ------------- | ------------------------------------------------------------------------- |

    ## What I'm currently learning 📚

    [LEARNINGS / INTERESTS]
    ```

    Make sure to only include the information you have in the resume content.
    Remember to make it fun and creative. Include emojis, colors, nice fonts and other creative elements.
    Only output the README content, nothing else.
    """
    if query:
        response = llm.invoke([
            {"role": "system", "content": content_prompt},
            {"role": "user", "content": f"Generate a README file based on this resume content and these very important additional instructions: {query}\n\nResume content:\n{resume_content}\n\nThe GitHub username is: {username}"}
        ])
    else:
        response = llm.invoke([
            {"role": "system", "content": content_prompt},
            {"role": "user", "content": f"Generate a README file based on this resume content:\n\n{resume_content}\n\nThe GitHub username is: {username}"}
        ])
    with open("temp/README.md", "w") as file:
        file.write(response)
    return response

@tool(args_schema=ProfileOptimizerInput)
def optimize_github_profile(url: str, resume_content: Optional[str] = None, llm: Optional[object] = None) -> str:
    """Optimize professional profiles (GitHub).
    
    Args:
        url: The profile URL to optimize
        resume_content: Optional string containing resume text content
        llm: Optional LLM instance to use (will create new one if not provided)

    Returns:
        str: Optimized profile content
    """
    llm = llm or TogetherLLM(temperature=0.1)

    content = get_github_profile(url, llm)
    print(f"GitHub profile content: {content}")
        
    parsed_resume = None
    if isinstance(resume_content, str):
        parsed_resume = parse_resume(resume_content, llm)
        if json.loads(parsed_resume).get("ERROR") == "NOT ENOUGH INFORMATION":
            return "Not enough information to optimize profile. Please provide the following information: " + json.loads(parsed_resume)["information_needed"]

    system_prompt = f"""You are an expert profile optimizer.
        You are a given GitHub profile and sometimes a resume.
        You need to optimize the profile based on the resume data and the profile content and provide advice on how to improve it.
        Make sure to include all the information you have and be creative and critical. But also mention what is particularly good in the profile.
        Try to focus on the most important information and on the keywords that are most relevant for the profile. Do not consider potential issues with pictures or images.
        Remember to optimize it for GitHub but do not include any links or URLs in your advice.
        Make your advice straight to the point and as constructive and organized (use bullet points and lists if needed) as possible.
        """
    if parsed_resume:
        return llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Optimize this GitHub profile:\n{content}\n\nResume data:\n{parsed_resume}"}
        ])
    else:
        return llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Optimize this GitHub profile: {content}"}
        ])

@tool
def get_current_github_readme(github_token: str, llm: Optional[object] = None) -> str:
    """Get the current GitHub README file."""
    llm = llm or TogetherLLM(temperature=0.1)
    try:    
        g = Github(github_token)
        user = g.get_user()
        repo_name = f"{user.login}/{user.login}"
        try:
            repo = g.get_repo(repo_name)
        except Exception as e:
            print(f"Error getting repository: {str(e)}")
            return "The profile repository does not exist yet."
        try:
            contents = repo.get_contents("README.md")
            return "Current README file:\n" + contents.decoded_content.decode("utf-8")
        except:
            return "The user does not have a profile README file yet."
    except Exception as e:
        return f"Error getting current GitHub README: {str(e)}, please check your GitHub token."


@tool
async def publish_to_github_pages(github_token: str, branch_name: str = "main") -> str:
    """Publish website files to GitHub Pages.

    Args:
        github_token: GitHub personal access token (REQUIRED)
        branch_name: The name of the branch to publish to (default: "main")
    """
    try:
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
                description="My Portfolio Website",
                homepage=f"https://{user.login}.github.io",
            )

        # Walk through temp directory and get all files
        temp_dir = "temp"
        files_to_publish = {}
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                # Get the full local path
                local_path = os.path.join(root, file)
                # Create the GitHub path by removing 'temp/' from the start
                github_path = os.path.relpath(local_path, temp_dir)
                files_to_publish[github_path] = local_path
                print(f"Found file to publish: {github_path}")

        # Create necessary directories first
        directories = set()
        for github_path in files_to_publish.keys():
            directory = os.path.dirname(github_path)
            if directory and directory not in directories:
                try:
                    repo.get_contents(directory)
                except:
                    repo.create_file(
                        f"{directory}/.gitkeep",
                        f"Create {directory} directory",
                        ""
                    )
                    print(f"Created directory: {directory}")
                directories.add(directory)

        # Update or create each file
        for github_path, local_path in files_to_publish.items():
            try:
                with open(local_path, 'rb') as file:
                    content = file.read()

                try:
                    # Try to update existing file
                    contents = repo.get_contents(github_path)
                    repo.update_file(
                        contents.path,
                        "Update portfolio website",
                        content,
                        contents.sha
                    )
                    print(f"Updated {github_path}")
                except:
                    # Create new file if it doesn't exist
                    repo.create_file(
                        github_path,
                        "Initial portfolio website",
                        content
                    )
                    print(f"Created {github_path}")
            except Exception as e:
                print(f"Error with {github_path}: {str(e)}")

        # Enable GitHub Pages if not already enabled
        # create/update the style.css file
        try:
            repo.edit(has_pages=True)
        except:
            print("Note: Could not automatically enable GitHub Pages. Please enable it in repository settings.")

        return f"Website successfully published! View it at: https://{user.login}.github.io\nNote: It may take a few minutes for changes to appear."
    
    except Exception as e:
        return f"Error publishing website: {str(e)}\nPlease check your GitHub token and permissions."

@tool
def publish_to_github_readme(github_token: str, readme_content: Optional[str] = None, llm: Optional[object] = None) -> str:
    """Publish a GitHub README file to a GitHub repository."""
    llm = llm or TogetherLLM(temperature=0.1)

    try:
        if not readme_content:
            with open("temp/README.md", "r") as file:
                readme_content = file.read()
        g = Github(github_token)
        user = g.get_user()
        repo_name = user.login

        try:
            repo = user.get_repo(repo_name)
        except:
            repo = user.create_repo(repo_name, description="My GitHub profile")
        
        try: 
            contents = repo.get_contents("README.md")
            repo.update_file(
                "README.md",
                "Update README",
                readme_content,
                contents.sha
            )
        except:
            repo.create_file(
                "README.md",
                "Initial README",
                readme_content
            )

        return f"README published at: https://github.com/{user.login}"

    except Exception as e:
        return f"Error publishing README: {str(e)}"


# Module-level singleton and initialization state
_router_instance = None
_initialized = False

class WebsiteRequestInput(BaseModel):
    """Input schema for website request routing."""
    user_input: str = Field(..., description="The user's request or preferences")
    resume_content: Optional[str] = Field(None, description="Optional resume content")
    llm: Optional[object] = Field(None, description="Optional LLM instance")

@tool
async def route_website_request(
    user_input: str,
    resume_content: Optional[str] = None,
    llm: Optional[object] = None
) -> str:
    """
    EVERY website request goes through here. This tool handles routing all website-related requests 
    to the appropriate generator (home page, education page, navigation, shared styles, etc.).
    """
        
    try:
        router = await get_router(resume_content)
        
        if not PageRouter.is_initialized():
            print("Initializing with user input:", user_input)
            await router.base_generator.generate_initial_shared_elements(user_input)
            PageRouter.set_initialized()
            return "Initial website design created based on your preferences!"
        
        return await router.handle_request(user_input)
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        print(f"Error type: {type(e)}")
        raise
