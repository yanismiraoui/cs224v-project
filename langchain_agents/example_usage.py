import asyncio
import os
from pathlib import Path
import logging
from typing import Optional
import toml
import PyPDF2
from agent import JobApplicationAgent

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeProcessor:
    def __init__(self, secrets_path: Optional[str] = None):
        self.secrets_path = secrets_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'secrets.toml'
        )
        self.agent = None
        self.setup_environment()

    def setup_environment(self) -> None:
        """Setup environment variables from secrets file."""
        try:
            secrets = toml.load(self.secrets_path)
            os.environ['GITHUB_TOKEN'] = secrets['GITHUB_TOKEN']
        except Exception as e:
            logger.error(f"Failed to load secrets: {str(e)}")
            raise

    @staticmethod
    def get_pdf_text(pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return " ".join(
                    page.extract_text() for page in pdf_reader.pages
                )
        except Exception as e:
            logger.error(f"Failed to read PDF file: {str(e)}")
            raise

    async def test_readme_operations(self, resume_text: str) -> None:
        """Test README-related operations."""
        try:
            logger.info("=== Testing README Operations ===")
            
            # Check current README
            response = await self.agent.process("What do you think of my current GitHub README?")
            logger.info(f"Current README Analysis: {response}")

            # Give the GitHub token
            response = await self.agent.process(f"This is my token {os.getenv('GITHUB_TOKEN')}")
            logger.info(f"GitHub Token: {response}")

            # Generate new README
            response = await self.agent.process("Generate a new GitHub README", 
                                              resume_content=resume_text)
            logger.info(f"README Generation: {response}")

            # Publish README
            response = await self.agent.process("Publish my README to GitHub")
            logger.info(f"README Publishing: {response}")

            # Optimize and republish
            response = await self.agent.process(
                "Make my readme more professional and do not include my research experienceand publish the new version to GitHub"
            )
            logger.info(f"README Optimization: {response}")

        except Exception as e:
            logger.error(f"README operations failed: {str(e)}")
            raise

    async def test_website_operations(self, resume_text: str) -> None:
        """Test website-related operations."""
        try:
            logger.info("=== Testing Website Operations ===")
            
            # Generate website
            response = await self.agent.process("Create a professional website", 
                                              resume_content=resume_text)
            logger.info(f"Website Generation: {response}")
            import sys
            sys.exit()

            # Publish to GitHub
            response = await self.agent.process("Publish to GitHub")
            logger.info(f"Website Publishing: {response}")

            # Give the GitHub token
            response = await self.agent.process(f"This is my token {os.getenv('GITHUB_TOKEN')}")
            logger.info(f"GitHub Token: {response}")

        except Exception as e:
            logger.error(f"Website operations failed: {str(e)}")
            raise

    async def run(self, resume_path: str, test_website: bool = False, test_readme: bool = False) -> None:
        """Main execution method."""
        try:
            self.agent = JobApplicationAgent()
            resume_text = self.get_pdf_text(resume_path)

            if test_website:
                await self.test_website_operations(resume_text)
            
            if test_readme:
                await self.test_readme_operations(resume_text)

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise

async def main():
    resume_path = Path('./cv_examples/CV Yanis MIRAOUI.pdf')
    processor = ResumeProcessor()
    
    try:
        await processor.run(
            resume_path=str(resume_path),
            test_website=True,  # Change this to True
            test_readme=True
        )
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())