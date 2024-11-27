from typing import Dict, Any, Optional, List
import json
from custom_together_llm import TogetherLLM
from .base_page_generator import BasePageGenerator
from .home_screen_generator import HomeScreenGenerator
from .education_page_generator import EducationPageGenerator

# Module-level singleton
_router_instance = None

async def get_router(resume_content: Optional[str] = None) -> 'PageRouter':
    """Get or create router instance with proper initialization."""
    global _router_instance
    
    if _router_instance is None:
        # First time creation - initialize everything
        _router_instance = PageRouter(resume_content)
        if resume_content:
            # Set resume and generate initial nav
            BasePageGenerator.set_resume(resume_content)
            await _router_instance.base_generator.parse_nav_sections()
    
    elif resume_content:
        # Just update existing router with new resume
        BasePageGenerator.set_resume(resume_content)
        await _router_instance.base_generator.parse_nav_sections()
    
    return _router_instance

class PageRouter:
    """Routes user requests to appropriate page generators."""
    
    _instance = None  # Class-level singleton instance
    _initialized = False  # Track if initial design is created
    
    def __new__(cls, resume_content: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(PageRouter, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, resume_content: Optional[str] = None):
        if not hasattr(self, 'initialized'):
            print("Initializing new PageRouter")
            self.llm = TogetherLLM(
                model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                temperature=0,
                max_tokens=2000
            )
            self.base_generator = BasePageGenerator()
            self.home_generator = HomeScreenGenerator()
            self.education_generator = EducationPageGenerator()
            
            # Map components to their generators and methods
            self.component_handlers = {
                'shared': (self.base_generator, 'update_shared_elements', 'create_shared_element'),
                'home': (self.home_generator, 'update_page', 'create_page_element'),
                'education': (self.education_generator, 'update_page', 'create_page_element')
            }
            
            if resume_content:
                self.initialize_with_resume(resume_content)
            self.initialized = True

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if initial design has been created."""
        return cls._initialized

    @classmethod
    def set_initialized(cls):
        """Mark router as initialized with initial design."""
        cls._initialized = True

    async def initialize_with_resume(self, resume_content: str):
        """First-time initialization with resume content."""
        print("First-time initialization with resume")
        BasePageGenerator.set_resume(resume_content)
        await self.base_generator.generate_initial_nav()

    async def handle_request(self, user_input: str) -> str:
        """Main entry point for all requests."""
        action_prompt = f"""Determine if this request is about creating something new or updating existing content.
User request: "{user_input}"
Return ONLY 'create' or 'update' based on the request type."""

        action = str(await self.llm.ainvoke([
            {"role": "system", "content": "Determine if a request is for creating new content or updating existing content."},
            {"role": "user", "content": action_prompt}
        ])).strip().lower()

        # Get appropriate method name based on action
        method_index = 2 if action == 'create' else 1
        
        # Route to appropriate handler
        return await self._route_request(user_input, action, method_index)

    async def _route_request(self, user_input: str, action: str, method_index: int) -> str:
        """Route requests to appropriate generators."""
        routing_prompt = f"""Analyze this request and identify which component each {action} is for.
User request: "{user_input}"

Components available:
- shared: for shared elements (navigation, background, colors, fonts, header/footer, layout)
- home: for home/about page content
- education: for education section content

Return a JSON dictionary where each key is the specific task and value is the component."""

        response = await self.llm.ainvoke([
            {"role": "system", "content": f"Break down website {action} requests into specific tasks and their handlers."},
            {"role": "user", "content": routing_prompt}
        ])

        tasks = json.loads(str(response).strip())
        
        # Handle each task and collect responses
        responses = []
        for task, component in tasks.items():
            try:
                if component in self.component_handlers:
                    generator, update_method, create_method = self.component_handlers[component]
                    method = getattr(generator, create_method if method_index == 2 else update_method)
                    result = await method(task)
                    responses.append(f"✓ {task}: {result}")
                else:
                    responses.append(f"✗ {task}: Unknown component {component}")
            except Exception as e:
                responses.append(f"✗ {task}: Error - {str(e)}")

        return "\n".join(responses)
    async def update_resume(self, resume_content: str):
        """Update the router with new resume content."""
        print("Updating resume content")
        BasePageGenerator.set_resume(resume_content)
        await self.base_generator.parse_nav_sections(resume_content)
