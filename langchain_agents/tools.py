from langchain.tools import tool
from github import Github

@tool
def generate_website_content(name: str, experience: list[str], skills: list[str]) -> str:
    """
    Generate professional website content based on user information
    Args:
        name: Name of the user
        experience: List of professional experience
        skills: List of skills
    """
    return f"Website content generated for {name}, with experience in {experience} and skills in {skills}"

@tool
def optimize_profile(url: str, profile_type: str) -> str:
    """
    Optimize professional profiles (LinkedIn/GitHub)
    Args:
        url: URL of the profile to optimize
        profile_type: Type of profile to optimize (e.g., 'LinkedIn', 'GitHub')
    """
    return f"Profile optimized for {url} of type {profile_type}"

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