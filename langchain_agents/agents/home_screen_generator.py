from custom_together_llm import TogetherLLM
from typing import Optional, Dict, Union, Any, List
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from dataclasses import dataclass
from datetime import datetime
import os
from PIL import Image
from .base_page_generator import BasePageGenerator

@dataclass
class Conversation:
    """Store conversation history and design preferences."""
    timestamp: datetime
    user_input: str
    design_preferences: Dict[str, Any]
    generated_code: Optional[Dict[str, str]] = None

class HomeScreenGenerator(BasePageGenerator):
    """Generates the home/about page content."""
    
    def __init__(self):
        super().__init__()
        self.personal_info = {}
        self.html = None
        self.css = None
        self.js = None
        self.profile_pic_path = "static/images/profile_pic.jpg"

    async def generate_home_screen(self, 
                                 user_input: str) -> str:
        """Generate the home screen based on user input."""
        try:
            # Parse resume for personal info
            parsed_info = await self._parse_resume()
            if parsed_info:
                self.personal_info = parsed_info
                print("Successfully extracted info from resume")

            # Parse user input for any additional preferences
            user_info = await self._parse_user_input(user_input)
            if user_info:
                self.personal_info.update({
                    k: v for k, v in user_info.items() if v
                })
                print(f"Updated personal information from user input: {user_info}")

            # # Check for missing required info
            # required_fields = ['name', 'role', 'bio', 'contact']
            # missing_fields = [
            #     field for field in required_fields 
            #     if not self.personal_info.get(field)
            # ]
            
            # if missing_fields:
            #     return {
            #         "status": "missing_info",
            #         "missing_fields": missing_fields,
            #         "message": f"I need your {missing_fields[0]} to continue."
            #     }

            # Generate or update design
            if not any([self.html, self.css, self.js]):
                await self._generate_initial_design(user_input)
            else:
                await self._update_design(user_input)

            # Save files if generated successfully
            if all([self.html, self.css, self.js]):
                temp_dir = "temp"
                os.makedirs(temp_dir, exist_ok=True)

                with open(os.path.join(temp_dir, "index.html"), "w") as f:
                    f.write(self.html.strip())
                with open(os.path.join(temp_dir, "style.css"), "w") as f:
                    f.write(self.css.strip())
                with open(os.path.join(temp_dir, "script.js"), "w") as f:
                    f.write(self.js.strip())

                return "Home page has been generated and saved successfully!"
            else:
                return "Failed to generate all required code components."

        except Exception as e:
            print(f"Generation error: {str(e)}")
            return f"Error generating home page: {str(e)}"

    async def _generate_initial_design(self, user_input: str) -> None:
        """Generate website code using separate calls for HTML, CSS, and JS."""
        try:
            # Generate HTML first
            self.html = await self._generate_html()
            
            # Generate CSS based on HTML
            self.css = await self._generate_css(self.html)
            
            # Generate JS based on HTML and CSS
            self.js = await self._generate_js(self.html, self.css)

        except Exception as e:
            print(f"Design generation error: {str(e)}")
            raise

    def _apply_fix(self, code: str, fix: str) -> str:
        """Apply a specific fix to the code."""
        try:
            # Here you could implement more sophisticated fix logic
            # For now, we'll just append the fix as a comment for review
            return f"{code}\n\n/* Suggested fix: {fix} */\n"
        except Exception as e:
            print(f"Error applying fix: {str(e)}")
            return code

    async def _generate_html(self) -> str:
        """Generate HTML file."""
        # Check for profile picture in temp/imgs folder
        profile_pic_exists = os.path.exists(os.path.join("temp", "imgs", "profile_pic.jpg"))
        
        profile_pic_section = ""
        if profile_pic_exists:
            profile_pic_section = """
            - Profile Picture: Include an img tag referencing imgs/profile_pic.jpg
            - Place profile picture prominently in the layout
            - Add proper alt text for accessibility"""

        html_prompt = f"""Create a clean HTML file for a personal website with these requirements:

Content (only generate sections for provided information, skip if not provided):
- Name: {self.personal_info.get('name')}
- Role: {self.personal_info.get('role')}
- Bio: {self.personal_info.get('bio')}
- Contact: {self.personal_info.get('contact')}

Note: Generate HTML sections ONLY for the information that is provided above. If any field is None or empty, do not create its corresponding section.

{profile_pic_section}

Structure:
1. Navigation:
   - Add iframe at top of body: <iframe src="navigation.html" frameborder="0" id="nav-frame"></iframe>
   - Add link to navigation.css in head section
   - Add link to navigation.js before end of body
   - The iframe should span full width and adjust height to content

2. Main content:
   {f'- Profile picture with class="profile-pic"' if profile_pic_exists else ''}
   - Name (h1)
   - Role (professional subtitle)
   - Section header "About Me" (h2)
   - Bio paragraph
   - Section header "Get In Touch" (h2) with hyperlinked contact info
   - Each contact method should be on a separate line

Requirements:
- Clean, semantic HTML
{f'- Include profile picture with src="imgs/profile_pic.jpg"' if profile_pic_exists else ''}
- Proper indentation
- Include particles-js container
- Link to external scripts (particles.js, gsap)
- MUST include link to style.css in the head section
- MUST include link to script.js at the end of body
- MUST include link to navigation.css in head section
- MUST include link to navigation.js before end of body

Return ONLY the HTML code with proper CSS and JS file references without any explanations, comments, or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are an HTML expert. Return only clean, semantic HTML code.
                DO NOT include:
                - No markdown code block markers (```)
                - No language identifiers
                - No explanations before or after the code
                - DO NOT generate navigation HTML, only include the iframe
                """
            },
            {"role": "user", "content": html_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_css(self, html: str) -> str:
        """Generate CSS file based on HTML structure and shared template."""
        # Get base styles from BasePageGenerator
        base_css = self.shared_css
        
        # Check for profile picture
        profile_pic_exists = os.path.exists("imgs/profile_pic.jpg")
        
        profile_pic_section = """
        Profile Picture Styling:
        - Set max-width: 200px
        - Set max-height: 200px
        - Create circular profile picture
        - Add white border
        - Use object-fit: cover
        - Position on the right side
        - Add subtle box shadow
        - Add responsive sizing""" if profile_pic_exists else ""

        css_prompt = f"""Enhance this base CSS with additional styles specific to the home page.
Base CSS:
{base_css}

HTML to style:
{html}

Additional requirements:
1. Keep ALL existing styles from base CSS
2. Add styles ONLY for elements not covered in base CSS
3. Maintain consistent:
   - Color scheme
   - Typography
   - Spacing patterns
   - Animation timings

{profile_pic_section}

Return the complete CSS including base styles and new additions."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a CSS expert. 
                - Preserve ALL base CSS
                - Add only new, non-conflicting styles
                - Maintain design consistency
                DO NOT include:
                - No markdown formatting
                - No explanations"""
            },
            {"role": "user", "content": css_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_js(self, html: str, css: str) -> str:
        """Generate JavaScript file based on HTML, CSS, and shared template."""
        # Get base JS from BasePageGenerator
        base_js = self.shared_js
        
        js_prompt = f"""Enhance this base JavaScript with additional functionality specific to the home page.
Base JavaScript:
{base_js}

HTML to enhance:
{html}

Requirements:
1. Keep ALL existing functionality from base JS
2. Maintain:
   - Particle effects
   - Animation patterns
   - Event handling structure
3. Add ONLY new functionality for:
   - Home-page specific animations
   - Additional interactions
   - Page-specific features

Return the complete JavaScript including base code and new additions."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a JavaScript expert.
                - Preserve ALL base JavaScript
                - Add only new, non-conflicting functionality
                - Maintain consistent patterns
                DO NOT include:
                - No markdown formatting
                - No explanations"""
            },
            {"role": "user", "content": js_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _update_design(self, user_input: str) -> None:
        """Update existing design based on user input."""
        try:
            if not all([self.html, self.css, self.js]):
                await self._generate_initial_design(user_input)
                return

            # Parse what needs to be updated
            updates_needed = await self._parse_update_request(user_input)
            print(f"Updates needed: {updates_needed}")
            # Update each component as needed
            if updates_needed.get('html'):
                self.html = await self._update_html(updates_needed['html'])
                
            if updates_needed.get('css'):
                self.css = await self._update_css(updates_needed['css'])
                
            if updates_needed.get('javascript'):
                self.js = await self._update_javascript(updates_needed['javascript'])

        except Exception as e:
            print(f"Error updating design: {str(e)}")
            raise

    async def _parse_resume(self) -> Optional[Dict[str, Any]]:
        """Parse resume for personal info only."""
        try:
            resume_content = self.get_resume()
            if not resume_content:
                print("No resume content found in parent class")
                return None

            info_response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": """You are a resume parser. For the role field, follow these rules:
1. If person is currently a student, use format: "[Degree] Student at [University]"
2. If employed, use their most recent job title: "[Title] at [Company]"
3. Always pick the CURRENT role (student or job)."""
                },
                {"role": "user", "content": f"""Extract these details from the resume:

1. Full name (usually at top)
2. Current role, following the rules above
3. Contact info (email, phone, LinkedIn)

Format EXACTLY like this:
name: John Smith
role: M.S. Computer Science Student at Stanford University
contact: email, phone, linkedin

Resume text:
{resume_content}"""}
            ])

            # Rest of the method remains the same...
            info_text = info_response['content'] if isinstance(info_response, dict) else info_response
            
            info_dict = {}
            for line in info_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info_dict[key.strip()] = value.strip()

            # Verify role is properly formatted
            if not info_dict.get('role') or info_dict.get('role') == 'Role Not Found':
                # Try a second attempt specifically for role
                role_response = await self.llm.ainvoke([
                    {
                        "role": "system",
                        "content": "Extract the current role (student or job) from this resume."
                    },
                    {"role": "user", "content": f"""Look for:
1. Current student status (check Education section for current enrollment)
2. Most recent job title (check Experience section)
3. Return the CURRENT role only

Format: "[Title/Degree] at [Institution/Company]"

Resume:
{resume_content}"""}
                ])
                
                role_text = role_response['content'] if isinstance(role_response, dict) else role_response
                info_dict['role'] = role_text.strip()

            # Get bio separately
            bio_response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": "Create a concise one-line professional bio."
                },
                {"role": "user", "content": f"Create a one-line professional bio from this resume:\n{resume_content}"}
            ])

            bio_text = bio_response['content'] if isinstance(bio_response, dict) else bio_response
            bio_text = bio_text.strip().strip('"')

            # Store the information
            return {
                "name": info_dict.get('name', ''),
                "role": info_dict.get('role', ''),
                "contact": info_dict.get('contact', ''),
                "bio": bio_text.strip()
            }

        except Exception as e:
            print(f"Resume parsing error: {str(e)}")
            return None

#     async def _parse_resume_sections(self, resume_content: str) -> List[str]:
#         """Extract major section headers from resume."""
#         section_prompt = f"""Extract the major section headers from this resume. 
# Return ONLY the section names in a comma-separated list.
# Common sections include: Education, Experience, Skills, Projects, Publications, etc.
# Do not include small subsections or individual entries.

# Resume:
# {resume_content}"""

#         try:
#             response = await self.llm.ainvoke([
#                 {
#                     "role": "system",
#                     "content": "Extract main section headers from resumes. Return only a comma-separated list."
#                 },
#                 {"role": "user", "content": section_prompt}
#             ])

#             # Get sections from response
#             content = response['content'] if isinstance(response, dict) else response
#             sections = [s.strip() for s in content.split(',')]
#             self.resume_sections = sections
#             return sections

#         except Exception as e:
#             print(f"Section parsing error: {str(e)}")
#             raise

    def _format_conversation_history(self) -> str:
        """Format recent conversation history."""
        if not self.conversation_history:
            return "No previous conversations"
        
        history = []
        for conv in self.conversation_history[-3:]:  # Last 3 conversations
            history.append(f"User: {conv.user_input}")
            if conv.design_preferences:
                history.append(f"Preferences: {json.dumps(conv.design_preferences, indent=2)}")
        
        return "\n".join(history)

    def _extract_code_block(self, text: str, language: str) -> str:
        """Extract and format code block for specific language."""
        try:
            if not isinstance(text, str):
                print(f"Unexpected response type: {type(text)}")
                return ""
                
            # Look for both variations of language markers
            start_markers = [f"```{language}", "```"]
            start = -1
            for marker in start_markers:
                start = text.find(marker)
                if start != -1:
                    start += len(marker)
                    break
                    
            if start == -1:
                print(f"Could not find start marker for {language}")
                return ""
            
            end = text.find("```", start)
            
            if end == -1:
                print(f"Could not find end marker for {language}")
                return ""
                
            code = text[start:end].strip()
            return code
            
        except Exception as e:
            print(f"Error extracting {language} code block: {str(e)}")
            return ""

    async def _parse_user_input(self, user_input: str) -> Optional[Dict[str, str]]:
        """Parse user input for personal information using LLM."""
        try:
            parse_prompt = f"""Extract the following information from this user message, if present:
- Name
- Role/Profession
- Bio/Description
- Contact Information (email, phone, or social media)

Format the response as a JSON object with these exact keys: name, role, bio, contact
If any information is missing, set its value to null.

User message: {user_input}"""

            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": "You are an expert at extracting personal information from text. Return only valid JSON."
                },
                {"role": "user", "content": parse_prompt}
            ])

            content = response['content'] if isinstance(response, dict) else response
            
            # Parse the JSON response
            try:
                parsed_info = json.loads(content)
                # Filter out None/null values
                return {k: v for k, v in parsed_info.items() if v}
            except json.JSONDecodeError:
                print("Failed to parse LLM response as JSON")
                return None

        except Exception as e:
            print(f"Error parsing user input: {str(e)}")
            return None 

    async def _check_and_create_required_files(self, js_code: str, temp_dir: str) -> None:
        """Analyze JS code and create any required configuration files."""
        try:
            analysis_prompt = f"""Analyze this JavaScript code and identify any external configuration files that need to be created.
            For each required file:
            1. Identify the filename
            2. Determine the expected content/format
            3. Generate appropriate configuration content

            JavaScript code:
            {js_code}

            Return your response in this format:
            REQUIRED_FILES:
            filename1: content
            filename2: content
            
            If no files are needed, return "NO_FILES_REQUIRED"
            """

            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": "You are an expert at analyzing JavaScript code and generating configuration files. If you generate JSON content, ensure it's valid JSON."
                },
                {"role": "user", "content": analysis_prompt}
            ])

            print("Creating required files...")
            content = response if isinstance(response, str) else response.get('content', '')
            
            if content.strip() == "NO_FILES_REQUIRED":
                return

            # Parse the response and create files
            current_file = None
            current_content = []
            
            for line in content.split('\n'):
                if line.startswith('REQUIRED_FILES:'):
                    continue
                elif line.strip().endswith(':'):
                    # Save previous file if exists
                    if current_file and current_content:
                        with open(os.path.join(temp_dir, current_file), 'w') as f:
                            f.write('\n'.join(current_content))
                    # Start new file
                    current_file = line.strip().rstrip(':')
                    current_content = []
                elif line.strip():
                    current_content.append(line)
            
            # Save last file
            if current_file and current_content:
                with open(os.path.join(temp_dir, current_file), 'w') as f:
                    f.write('\n'.join(current_content))

        except Exception as e:
            print(f"Error creating required files: {str(e)}") 

    async def _parse_update_request(self, user_input: str) -> Dict[str, str]:
        """Parse user request to determine which files need updates."""
        parse_prompt = f"""Analyze this user request and determine which website components need to be updated.
User request: "{user_input}"

Identify changes needed for HTML, CSS, and/or JavaScript.
Return ONLY a JSON object with these keys:
- html: description of HTML changes needed (or null if none)
- css: description of CSS changes needed (or null if none)
- javascript: description of JavaScript changes needed (or null if none)

Example:
{{
    "html": "Update the bio text and add social media links",
    "css": "Change the color scheme to blue",
    "javascript": null
}}"""

        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": "You are an expert at analyzing web development change requests. Return only valid JSON."
                },
                {"role": "user", "content": parse_prompt}
            ])

            content = response if isinstance(response, str) else response.get('content', '')
            return json.loads(content)

        except Exception as e:
            print(f"Error parsing update request: {str(e)}")
            raise

    async def _update_html(self, change_description: str) -> str:
        """Update HTML based on specific changes needed."""
        update_prompt = f"""Update this HTML code according to the following changes:
Change description: {change_description}

Current HTML:
{self.html}

CRITICAL REQUIREMENTS:
- ONLY modify elements specifically mentioned in the change description
- DO NOT add any new sections or elements unless explicitly requested
- DO NOT modify any other content
- DO NOT change structure unless specifically asked
- Preserve all existing content and formatting not mentioned
- Return the complete HTML with ONLY the requested changes

Return the HTML code with only the specified changes."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are an HTML expert. Make ONLY the requested changes. Do not modify anything else.
                DO NOT include:
                - No markdown code block markers (```)
                - No language identifiers
                - No explanations before or after the code"""
            },
            {"role": "user", "content": update_prompt}
        ])

        print(f"Updated HTML: {response}")

        return response if isinstance(response, str) else response.get('content', '')

    async def _update_css(self, change_description: str) -> str:
        """Update CSS based on specific changes needed."""
        update_prompt = f"""Update this CSS code according to the following changes:
Change description: {change_description}

Current CSS:
{self.css}

CRITICAL REQUIREMENTS:
- ONLY modify styles specifically mentioned in the change description
- DO NOT add any new styles unless explicitly requested
- DO NOT modify any other styles
- DO NOT change existing structure unless specifically asked
- Preserve all existing styles not mentioned
- Return the complete CSS with ONLY the requested changes

Return the CSS code with only the specified changes without any explanations, comments, or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a CSS expert. Make ONLY the requested changes. Do not modify anything else.
                DO NOT include:
                - No markdown code block markers (```)
                - No language identifiers
                - No explanations before or after the code"""
            },
            {"role": "user", "content": update_prompt}
        ])

        print(f"Updated CSS: {response}")

        return response if isinstance(response, str) else response.get('content', '')

    async def _update_javascript(self, change_description: str) -> str:
        """Update JavaScript based on specific changes needed."""
        update_prompt = f"""Update this JavaScript code according to the following changes:
Change description: {change_description}

Current JavaScript:
{self.js}

CRITICAL REQUIREMENTS:
- ONLY modify functionality specifically mentioned in the change description
- DO NOT add any new functions unless explicitly requested
- DO NOT modify any other functionality
- DO NOT change existing logic unless specifically asked
- Preserve all existing code not mentioned
- Return the complete JavaScript with ONLY the requested changes

Return the JavaScript code with only the specified changes without any explanations, comments, or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a JavaScript expert. Make ONLY the requested changes. Do not modify anything else.
                DO NOT include:
                - No markdown code block markers (```)
                - No language identifiers
                - No explanations before or after the code"""
            },
            {"role": "user", "content": update_prompt}
        ])

        print(f"Updated JavaScript: {response}")

        return response if isinstance(response, str) else response.get('content', '') 