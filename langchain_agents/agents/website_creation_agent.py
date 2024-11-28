from typing import Dict, List, Optional
from pathlib import Path
import json
from custom_together_llm import TogetherLLM

class WebsiteCreationAgent:
    def __init__(self):
        self.llm = TogetherLLM(temperature=0.7)
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
    def _parse_resume(self, resume_content: str) -> Dict:
        """Parse resume to determine required sections."""
        prompt = """You are a JSON generator. Your only task is to analyze the resume and output a valid JSON object.

        Analyze this resume and determine the most impactful sections for a personal website.
        Output a JSON object with:
        1. Recommended sections (always include Home)
        2. Key information for each section
        3. A single, consistent design theme

        Required JSON structure:
        {
            "sections": ["Home", "..."],
            "section_content": {
                "Home": {
                    "name": "...",
                    "title": "...",
                    "brief_intro": "..."
                },
                "additional_section": {
                    "relevant_content": "..."
                }
            },
            "design_theme": {
                "color_scheme": ["primary", "secondary", "accent"],
                "typography": {"heading_font": "...", "body_font": "..."},
                "style": "minimal/modern/etc",
                "layout_preference": "..."
            }
        }

        IMPORTANT: Return ONLY the JSON object. No additional text, explanations, or markdown formatting.
        """
        
        try:
            result = self.llm.invoke([
                {"role": "system", "content": prompt},
                {"role": "user", "content": resume_content}
            ])
            
            # Clean the response to ensure it's valid JSON
            result = result.strip()
            if result.startswith("```json"):
                result = result.split("```json")[1].split("```")[0].strip()
            elif result.startswith("```"):
                result = result.split("```")[1].split("```")[0].strip()
            
            return json.loads(result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {result}")
        except Exception as e:
            raise ValueError(f"Error parsing resume: {str(e)}")

    def _generate_page(self, section: str, content: Dict, shared_design: Dict) -> Dict[str, str]:
        """Generate HTML, CSS, and JS for a specific page."""
        # Check if profile picture exists
        profile_pic_exists = (self.temp_dir / "imgs" / "profile_pic.jpg").exists()
        
        if section == "Home":
            prompt = f"""Create a Home page that uses a shared navigation structure.
            Use this content: {json.dumps(content)}
            Follow these design guidelines: {json.dumps(shared_design)}
            
            Main content requirements:
            {f'- Profile picture with class="profile-pic"' if profile_pic_exists else ''}
            - Name (h1)
            - Role (professional subtitle)
            - Section header "About Me" (h2)
            - Bio paragraph
            - Section header "Get In Touch" (h2) with hyperlinked contact info
            - Each contact method should be on a separate line
            
            The HTML should:
            1. Include a consistent header structure with nav placeholder
            2. Use clean, semantic HTML
            {f'3. Include profile picture with src="imgs/profile_pic.jpg"' if profile_pic_exists else ''}
            4. Include particles-js container
            5. Use this basic structure:
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Home</title>
                    <link rel="stylesheet" href="shared.css">
                    <link rel="stylesheet" href="style.css">
                </head>
                <body>
                    <div id="particles-js"></div>
                    <header id="main-header">
                        <nav id="main-nav"></nav>
                    </header>
                    <main>
                        [Page Content Here]
                    </main>
                    <footer>
                        [Footer Content]
                    </footer>
                    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
                    <script src="shared.js"></script>
                    <script src="script.js"></script>
                </body>
                </html>
            """
        else:
            prompt = f"""Create a {section} page that uses a shared navigation structure.
            Use this content: {json.dumps(content)}
            Follow these design guidelines: {json.dumps(shared_design)}
            
            The HTML should:
            1. Include a consistent header structure with nav placeholder
            2. Use this basic structure:
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{section}</title>
                    <link rel="stylesheet" href="shared.css">
                    <link rel="stylesheet" href="{section.lower().replace(' ', '_')}.css">
                </head>
                <body>
                    <header id="main-header">
                        <nav id="main-nav"></nav>
                    </header>
                    <main>
                        [Page Content Here]
                    </main>
                    <footer>
                        [Footer Content]
                    </footer>
                    <script src="shared.js"></script>
                    <script src="{section.lower().replace(' ', '_')}.js"></script>
                </body>
                </html>
            """

        response = self.llm.invoke([
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate the page code"}
        ])

        # Extract code blocks
        html = response.split("```html")[1].split("```")[0].strip()
        css = response.split("```css")[1].split("```")[0].strip()
        js = response.split("```javascript")[1].split("```")[0].strip()

        return {
            "html": html,
            "css": css,
            "js": js
        }

    def _save_page(self, section: str, code: Dict[str, str]):
        """Save page files to temp directory."""
        section_name = section.lower().replace(" ", "_")
        
        # Save HTML
        html_path = self.temp_dir / f"{section_name}.html"
        html_path.write_text(code["html"])
        
        # Save CSS
        css_path = self.temp_dir / f"{section_name}.css"
        css_path.write_text(code["css"])
        
        # Save JavaScript
        js_path = self.temp_dir / f"{section_name}.js"
        js_path.write_text(code["js"])

    def _generate_shared_assets(self, design_theme: Dict, sections: List[str]):
        """Generate shared CSS and JS files with consistent navigation."""
        shared_css_prompt = """Create a shared CSS file that includes:
        1. Navigation bar styles:
           - Fixed position at top
           - Responsive design
           - Dropdown for mobile
        2. Common layout structures:
           - Header
           - Main content area
           - Footer
        3. Design system using:
           - CSS custom properties for colors
           - Typography scale
           - Spacing system
           - Component patterns
        4. Responsive breakpoints
        5. Smooth transitions
        
        Based on this design theme: ${json.dumps(design_theme)}"""
        
        shared_js_prompt = f"""Create a shared JavaScript file that:
        1. Automatically builds navigation on page load:
           - Uses the following sections: {json.dumps(sections)}
           - Creates nav links dynamically
           - Highlights current page
        2. Handles responsive behavior:
           - Mobile menu toggle
           - Dropdown functionality
        3. Implements:
           - Page transitions
           - Active state management
           - Smooth scrolling
        
        Include this structure:
        const nav_config = {json.dumps(sections)};
        
        function buildNavigation() {{
            const nav = document.getElementById('main-nav');
            nav_config.forEach(page => {{
                // Create nav items
            }});
        }}
        
        document.addEventListener('DOMContentLoaded', buildNavigation);"""
        
        shared_css = self.llm.invoke([
            {"role": "system", "content": shared_css_prompt},
            {"role": "user", "content": "Generate shared CSS"}
        ])
        
        shared_js = self.llm.invoke([
            {"role": "system", "content": shared_js_prompt},
            {"role": "user", "content": "Generate shared JavaScript"}
        ])

        # Save shared assets
        (self.temp_dir / "shared.css").write_text(shared_css.split("```css")[1].split("```")[0].strip())
        (self.temp_dir / "shared.js").write_text(shared_js.split("```javascript")[1].split("```")[0].strip())

    async def create_website(self, resume_content: str) -> Dict[str, List[str]]:
        """Create a complete personal website based on resume content."""
        try:
            # Parse resume and determine sections
            structure = self._parse_resume(resume_content)
            
            # Generate shared assets with sections
            self._generate_shared_assets(structure["design_theme"], structure["sections"])
            
            # Generate each page
            created_files = []
            for section in structure["sections"]:
                section_content = structure["section_content"].get(section, {})
                
                # Generate page code
                page_code = self._generate_page(
                    section,
                    section_content,
                    structure["design_theme"]
                )
                
                # Save page files
                self._save_page(section, page_code)
                
                # Track created files
                section_name = section.lower().replace(" ", "_")
                created_files.extend([
                    f"{section_name}.html",
                    f"{section_name}.css",
                    f"{section_name}.js"
                ])

            return {
                "status": "success",
                "created_files": created_files,
                "sections": structure["sections"]
            }

        except Exception as e:
            print(f"Error creating website: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def modify_page(self, page_name: str, modifications: str) -> Dict[str, str]:
        """Modify an existing page based on user request."""
        try:
            # Shared assets
            shared_css = (self.temp_dir / "shared.css").read_text()
            shared_js = (self.temp_dir / "shared.js").read_text()

            # Read existing files
            page_name = page_name.lower().replace(" ", "_")
            html_path = self.temp_dir / f"{page_name}.html"
            css_path = self.temp_dir / f"{page_name}.css"
            js_path = self.temp_dir / f"{page_name}.js"


            existing_html = html_path.read_text() if html_path.exists() else ""
            existing_css = css_path.read_text() if css_path.exists() else ""
            existing_js = js_path.read_text() if js_path.exists() else ""

            # Generate modification prompt
            prompt = f"""Modify this page according to: {modifications}

            Shared CSS:
            {shared_css}
            
            Shared JS:
            {shared_js}
            
            Existing HTML:
            {existing_html}
            
            Existing CSS:
            {existing_css}
            
            Existing JS:
            {existing_js}
            
            Return only the modified code blocks that need to change.
            Maintain consistency with shared.css and shared.js.
            Preserve existing functionality while adding new features.
            Ensure responsive design remains intact."""

            # Get modifications
            response = self.llm.invoke([
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Generate modifications"}
            ])

            # Extract and apply modifications
            modified_code = {
                "html": response.split("```html")[1].split("```")[0].strip() if "```html" in response else existing_html,
                "css": response.split("```css")[1].split("```")[0].strip() if "```css" in response else existing_css,
                "js": response.split("```javascript")[1].split("```")[0].strip() if "```javascript" in response else existing_js
            }

            # Save modified files
            self._save_page(page_name, modified_code)

            return {
                "status": "success",
                "message": f"Successfully modified {page_name}"
            }

        except Exception as e:
            print(f"Error modifying page: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
