from custom_together_llm import TogetherLLM
from typing import List
import os

class BasePageGenerator:
    """Base class for shared website elements."""
    
    _instance = None  # Singleton instance
    _resume_content = None  # Shared resume content
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BasePageGenerator, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.llm = TogetherLLM(
                model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                temperature=0,
                max_tokens=4000
            )
            self.shared_css = None
            self.shared_js = None
            self.nav_items = None
            self.nav_html = None
            self.nav_css = None
            self.nav_js = None
            self.initialized = True

    @classmethod
    def set_resume(cls, content: str):
        """Set shared resume content."""
        cls._resume_content = content

    @classmethod
    def get_resume(cls) -> str:
        """Get shared resume content."""
        return cls._resume_content

    @classmethod
    def has_resume(cls) -> bool:
        """Check if resume content is initialized."""
        return cls._resume_content is not None

    async def parse_nav_sections(self) -> List[str]:
        """Initial parsing of navigation sections from resume."""
        if not self._resume_content:
            raise ValueError("Resume content not initialized")
            
        prompt = f"""Analyze this resume and determine the main sections for website navigation.
Requirements:
1. "About Me" must be the first section. It must link to index.html
2. Include only major sections that would make good web pages
3. Use clear, concise section names
4. Consider common portfolio sections like Education, Skills, Experience
5. Maintain professional naming conventions

Resume content:
{self._resume_content}

Return ONLY a list of section names, one per line."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an expert at analyzing resume structure. Return only a simple list of section names."
            },
            {"role": "user", "content": prompt}
        ])

        # Clean and process the response
        sections = [
            line.strip() for line in str(response).split('\n')
            if line.strip() and not line.startswith('```')
        ]
        
        # Ensure "About Me" is first
        if "About Me" in sections:
            sections.remove("About Me")
        self.nav_items = ["About Me"] + sections
        return self.nav_items

    async def generate_initial_shared_elements(self, user_input: str) -> None:
        """Generate initial shared CSS and JS based on user preferences."""
        try:
            # First parse navigation sections from resume
            if not self.nav_items:
                await self.parse_nav_sections()
            
            # Generate navigation components
            await self.generate_navigation()
            
            # Generate shared CSS and JS
            self.shared_css = await self._generate_shared_css(user_input)
            self.shared_js = await self._generate_shared_js(user_input)
            
            # Save all files
            await self._save_shared_files()
        except Exception as e:
            print(f"Error generating shared elements: {str(e)}")
            raise

    async def _generate_shared_css(self, user_input: str) -> str:
        """Generate initial shared CSS incorporating user preferences."""
        css_prompt = f"""Create modern CSS for a professional portfolio website.

Core Requirements:
1. Color Scheme:
   - High contrast for readability
   - Accent colors for interactive elements
   - CSS variables for colors

2. Typography:
   - Modern, clean font stack
   - Responsive font sizes using rem
   - Clear hierarchy with distinct heading styles
   - Comfortable line heights and spacing

3. Layout & Structure:
   - CSS Grid and Flexbox for modern layouts
   - Mobile-first responsive design
   - Smooth transitions and animations
   - Clean spacing using consistent units

4. Components:
   - Stylish navigation bar with hover effects
   - Card designs for projects/sections
   - Button and link hover animations
   - Form styling if needed

5. Effects:
   - Subtle shadows for depth
   - Smooth transitions on interactions
   - Gradient accents where appropriate
   - Modern scrollbar styling

6. Technical Requirements:
   - Use CSS variables for maintainability
   - Include vendor prefixes
   - Optimize for performance
   - Follow BEM naming convention

IMPORTANT: While these are the base requirements, the user has specified their preferences as:
"{user_input}"
These preferences should override any conflicting base requirements. Particularly focus on any specific:
- Color schemes
- Layout preferences
- Animation styles
- Design elements
mentioned in the user input.

Return ONLY the CSS code without any explanations or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Return only clean, modern CSS code."
            },
            {"role": "user", "content": css_prompt}
        ])

        return self._clean_code_block(response)

    async def _generate_shared_js(self, user_input: str) -> str:
        """Generate initial shared JavaScript incorporating user preferences."""
        js_prompt = f"""Create modern JavaScript for a professional portfolio website.

Core Requirements:
1. Particles Background:
   - Dynamic particles.js configuration
   - Responsive to screen size
   - Performance optimized
   - Color scheme matching theme

2. Navigation & Menu:
   - Smooth scrolling to sections
   - Active section highlighting
   - Mobile menu toggle with animation
   - Scroll progress indicator

3. Animations & Transitions:
   - Intersection Observer for scroll animations
   - Smooth page transitions
   - Element hover effects
   - Loading animations

4. Interactive Elements:
   - Button click effects
   - Form validation and feedback
   - Custom cursor effects
   - Tooltip functionality

5. Performance & UX:
   - Lazy loading for images
   - Debounced scroll handlers
   - Preload critical resources
   - Error handling for all features

6. Technical Requirements:
   - Modern ES6+ syntax
   - Event delegation where appropriate
   - Clean error handling
   - Performance optimization
   - Mobile device support

IMPORTANT: While these are the base requirements, the user has specified their preferences as:
"{user_input}"
These preferences should override any conflicting base requirements. Particularly focus on any specific:
- Animation preferences
- Interactive features
- Performance requirements
- Special effects
mentioned in the user input.

Return ONLY the JavaScript code without any explanations or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a JavaScript expert. Return only clean, modern JavaScript code."
            },
            {"role": "user", "content": js_prompt}
        ])

        return self._clean_code_block(response)

#     async def generate_nav_html(self, current_page: str) -> str:
#         """Generate navigation HTML with current page marked as active."""
#         nav_prompt = f"""Create HTML for the navigation bar:

# Current page: {current_page}
# Navigation items: {self.nav_items}

# Requirements:
# 1. Mark current page as active
# 2. Convert spaces to underscores and lowercase for filenames
# 3. Link "About Me" to index.html
# 4. Other items link to their respective .html files
# 5. Include mobile-friendly structure

# Return ONLY the HTML code without any explanations or markdown formatting."""

#         response = await self.llm.ainvoke([
#             {
#                 "role": "system",
#                 "content": "You are an HTML expert. Return only clean HTML code."
#             },
#             {"role": "user", "content": nav_prompt}
#         ])

#         return self._clean_code_block(response if isinstance(response, str) else response.get('content', ''))


    async def update_nav_sections(self, change_description: str) -> List[str]:
        """Update navigation sections based on specific changes needed."""
        if not self.nav_items:
            raise ValueError("Navigation sections not initialized. Run parse_nav_sections first.")

        sections_list = '\n'.join(self.nav_items)
        update_prompt = f"""Update these navigation sections according to the changes requested.

Current sections:
{sections_list}

Change description: {change_description}

Requirements:
1. Keep "About Me" as the first section
2. Maintain professional naming conventions
3. Only make changes specified in the description
4. Return complete list of sections, not just changes
5. Ensure each section would make a logical web page

Return ONLY the updated section names, one per line."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an expert at website navigation structure. Return only a simple list of section names."
            },
            {"role": "user", "content": update_prompt}
        ])

        # Clean and process the response
        sections = [
            line.strip() for line in str(response).split('\n')
            if line.strip() and not line.startswith('```')
        ]
        
        # Ensure "About Me" is first
        if "About Me" in sections:
            sections.remove("About Me")
        self.nav_items = ["About Me"] + sections
        return self.nav_items
    
    
    async def update_shared_css(self, change_description: str) -> None:
        """Update shared CSS based on specific changes needed."""
        update_prompt = f"""Update the shared CSS according to these changes:
Change description: {change_description}

Current CSS:
{self.shared_css}

CRITICAL REQUIREMENTS:
- ONLY modify styles mentioned in the change description
- Preserve all other existing styles
- Return the complete CSS with ONLY the requested changes

Return ONLY the CSS code without any explanations or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Make ONLY the requested changes."
            },
            {"role": "user", "content": update_prompt}
        ])

        self.shared_css = self._clean_code_block(response if isinstance(response, str) else response.get('content', ''))
        await self._save_shared_files()

    async def update_shared_js(self, change_description: str) -> None:
        """Update shared JavaScript based on specific changes needed."""
        update_prompt = f"""Update the shared JavaScript according to these changes:
Change description: {change_description}

Current JavaScript:
{self.shared_js}

CRITICAL REQUIREMENTS:
- ONLY modify functionality mentioned in the change description
- Preserve all other existing code
- Return the complete JavaScript with ONLY the requested changes

Return ONLY the JavaScript code without any explanations or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a JavaScript expert. Make ONLY the requested changes."
            },
            {"role": "user", "content": update_prompt}
        ])

        self.shared_js = self._clean_code_block(response if isinstance(response, str) else response.get('content', ''))
        await self._save_shared_files()

    async def _save_shared_files(self) -> None:
        """Save shared CSS and JS files."""
        try:
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)

            if self.shared_css:
                with open(os.path.join(temp_dir, "shared.css"), "w") as f:
                    f.write(self.shared_css.strip())

            if self.shared_js:
                with open(os.path.join(temp_dir, "shared.js"), "w") as f:
                    f.write(self.shared_js.strip())

        except Exception as e:
            print(f"Error saving shared files: {str(e)}")
            raise

    def _clean_code_block(self, text: str) -> str:
        """Remove markdown formatting and explanatory text from code."""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        in_code_block = True
        
        for line in lines:
            if line.strip().startswith('```'):
                continue
            if line.strip().startswith('This') or line.strip().startswith('The above'):
                break
            if in_code_block:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip() 

    async def update_shared_elements(self, user_input: str) -> str:
        """Route updates to appropriate shared element handlers."""
        
        element_prompt = f"""Determine which shared element needs to be updated.
User request: "{user_input}"

Shared elements:
- navigation (navigation items)
- css (colors, fonts, layout, background, typography)
- javascript (animations, interactions)

Return ONLY the element name: 'navigation', 'css', or 'javascript'."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "Determine which shared website element needs updating."
            },
            {"role": "user", "content": element_prompt}
        ])

        element = str(response).strip().lower()

        try:
            match element:
                case 'navigation':
                    await self.update_nav_sections(user_input)
                    return "Updated navigation structure"
                case 'css':
                    await self.update_shared_css(user_input)
                    return "Updated shared CSS styles"
                case 'javascript':
                    await self.update_shared_js(user_input)
                    return "Updated shared JavaScript"
                case _:
                    return f"Unknown shared element: {element}"
        except Exception as e:
            return f"Error updating {element}: {str(e)}" 

    async def generate_navigation(self) -> None:
        """Generate all navigation components (HTML, CSS, JS) in sequence."""
        if not self.nav_items:
            await self.parse_nav_sections()
            
        # Generate in sequence so each can reference previous components
        self.nav_html = await self._generate_nav_html()
        self.nav_css = await self._generate_nav_css()
        self.nav_js = await self._generate_nav_js()
        
        # Save all navigation files
        await self._save_shared_files()

    async def _generate_nav_html(self) -> str:
        """Generate navigation HTML with navigation-specific CSS and JS references."""
        nav_prompt = f"""Create a complete HTML document for the navigation bar with these requirements:

1. Document Structure:
   - Complete HTML5 document structure
   - Include navigation-specific CSS and JS references
   - Meta tags for proper rendering

2. Head Section:
   - Charset UTF-8
   - Viewport meta tag
   - MUST include: <link rel="stylesheet" href="navigation.css">

3. Navigation Content:
   - Nav element with class="nav"
   - Container div with class="nav-container"
   - Unordered list with class="nav-list"
   - List items with class="nav-item" and data-page attributes
   - Links with class="nav-link"

4. Navigation Items:
{self.nav_items}

5. Mobile Menu:
   - Include mobile menu container
   - Add necessary structure for mobile responsiveness

6. Scripts:
   - MUST include: <script src="navigation.js"></script> at the end of body

Return a complete HTML document with navigation-specific references.
"""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are an HTML expert. Return a complete HTML document with navigation-specific references.
                MUST include:
                - <link rel="stylesheet" href="navigation.css"> in head
                - <script src="navigation.js"></script> at end of body
                DO NOT include:
                - No markdown code block markers
                - No language identifiers
                - No explanations
                - No other CSS/JS references"""
            },
            {"role": "user", "content": nav_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_nav_css(self) -> str:
        css_prompt = f"""Create CSS specifically for this navigation HTML:

{self.nav_html}

Requirements:
1. Position at the top of the website:
   - Fixed position
   - Full width background
   - Top: 0

2. Horizontal layout:
   - Display nav items in a single row
   - Use flexbox with justify-content: center
   - Equal spacing between items
   - No bullet points or list styling

3. Visual style:
   - Clean background color
   - Padding: 1rem vertical, 2rem horizontal
   - Border-bottom for separation
   - Container width: 80% max-width
   - Centered within the page

4. Nav items:
   - Display: inline-block
   - Horizontal padding between items
   - No text decoration on links
   - Smooth hover transitions
   - Modern font styling

5. Responsive design:
   - Collapse to hamburger on mobile
   - Maintain horizontal center on all screens
   - Smooth mobile menu transitions
   - Proper spacing in both desktop/mobile

IMPORTANT: Use the exact classes and IDs from the provided HTML above.
Return ONLY the CSS code."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Return only clean CSS code."
            },
            {"role": "user", "content": css_prompt}
        ])
        return self._clean_code_block(response)

    async def _generate_nav_js(self) -> str:
        js_prompt = f"""Create JavaScript for this navigation structure:

HTML:
{self.nav_html}

CSS:
{self.nav_css}

Requirements:
1. Mobile menu toggle
2. Smooth scrolling to sections
3. Active state management
4. Window resize handling
5. Accessibility support
6. Event delegation for efficiency
7. Error handling
8. Clean, modern ES6+ syntax
9. Menu item hover effects:
   - Add highlight class on hover
   - Remove highlight when mouse leaves
   - Smooth transition for highlight effect
   - Work for both desktop and mobile views

IMPORTANT: Use the exact classes and IDs from the provided HTML and CSS above.
Return ONLY the JavaScript code."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a JavaScript expert. Return only clean JavaScript code."
            },
            {"role": "user", "content": js_prompt}
        ])
        return self._clean_code_block(response)

    async def _save_shared_files(self) -> None:
        """Save all shared files including navigation components."""
        try:
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)

            # Save shared files
            if self.shared_css:
                with open(os.path.join(temp_dir, "shared.css"), "w") as f:
                    f.write(self.shared_css.strip())

            if self.shared_js:
                with open(os.path.join(temp_dir, "shared.js"), "w") as f:
                    f.write(self.shared_js.strip())

            # Save navigation files
            if self.nav_html:
                with open(os.path.join(temp_dir, "navigation.html"), "w") as f:
                    f.write(self.nav_html.strip())
                    
            if self.nav_css:
                with open(os.path.join(temp_dir, "navigation.css"), "w") as f:
                    f.write(self.nav_css.strip())
                    
            if self.nav_js:
                with open(os.path.join(temp_dir, "navigation.js"), "w") as f:
                    f.write(self.nav_js.strip())

        except Exception as e:
            print(f"Error saving shared files: {str(e)}")
            raise 