from custom_together_llm import TogetherLLM
from typing import Optional, Dict, Union, Any, List
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from dataclasses import dataclass
from datetime import datetime
import os
from PIL import Image

@dataclass
class Conversation:
    """Store conversation history and design preferences."""
    timestamp: datetime
    user_input: str
    design_preferences: Dict[str, Any]
    generated_code: Optional[Dict[str, str]] = None

class HomeScreenGenerator:
    """Generates the home/about page content."""
    
    def __init__(self):
        self.llm = TogetherLLM(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            temperature=0,
        )
        self.personal_info = {}
        self.html = None
        self.css = None
        self.js = None
        self.profile_pic_path = "static/images/profile_pic.jpg"

    async def generate_home_screen(self, 
                                 user_input: str,
                                 resume_content: str = None) -> str:
        """Generate the home screen based on user input."""
        try:
            # 1. Parse resume if provided
            if resume_content:
                parsed_info = await self._parse_resume(resume_content)
                if parsed_info:
                    self.personal_info = parsed_info
                    print("Successfully extracted info from resume")
                    
                sections = await self._parse_resume_sections(resume_content)
                if sections:
                    self.personal_info['sections'] = sections
                    print("Successfully extracted sections from resume")

            # 2. Parse user input for any personal information
            user_info = await self._parse_user_input(user_input)
            if user_info:
                # Update personal_info with any new information
                self.personal_info.update({
                    k: v for k, v in user_info.items() if v
                })
                print(f"Updated personal information from user input: {user_info}")

            # 3. Check for missing required info
            required_fields = ['name', 'role', 'bio', 'contact']
            missing_fields = [
                field for field in required_fields 
                if not self.personal_info.get(field)
            ]
            
            if missing_fields:
                return {
                    "status": "missing_info",
                    "missing_fields": missing_fields,
                    "message": f"""I need your {missing_fields[0]} to continue.

Please type it directly (e.g., "My {missing_fields[0]} is...")"""
                }

            # 4. Generate or update design
            response = None
            if not any([self.html, self.css, self.js]):
                await self._generate_initial_design(user_input)
            else:
                print("Updating design...")
                await self._update_design(user_input)

            # If we have a valid response, save the files
            if all([self.html, self.css, self.js]):
            # Save files to temp folder
                temp_dir = "temp"
                os.makedirs(temp_dir, exist_ok=True)

                with open(os.path.join(temp_dir, "index.html"), "w") as f:
                    f.write(self.html.strip())
                
                with open(os.path.join(temp_dir, "style.css"), "w") as f:
                    f.write(self.css.strip())
                
                with open(os.path.join(temp_dir, "script.js"), "w") as f:
                    f.write(self.js.strip())

                # await self._check_and_create_required_files(self.js, temp_dir)
                
                return "Home page has been generated and saved successfully! You can now publish it to GitHub Pages."
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
        
        sections = self.personal_info.get('sections', [])
        nav_links = []
        for section in sections:
            section_filename = section.lower().replace(" ", "_") + ".html"
            if section.lower() == "about me":
                nav_links.append('- "About Me" links to index.html')
            else:
                nav_links.append(f'- "{section}" links to {section_filename}')


        html_prompt = f"""Create a clean HTML file for a personal website with these requirements:

Content:
- Name: {self.personal_info.get('name')}
- Role: {self.personal_info.get('role')}
- Bio: {self.personal_info.get('bio')}
- Contact: {self.personal_info.get('contact')}
{profile_pic_section}

Structure:
1. Navigation bar with:
  - The "About Me" link MUST point to index.html
  - Each nav item MUST be an <a> tag with href to its corresponding HTML file
  - Navigation links MUST follow this EXACT pattern (except for the "About Me" link):
     {chr(10).join(nav_links)}

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

Return ONLY the HTML code with proper CSS and JS file references without any explanations, comments, or markdown formatting. """

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are an HTML expert. Return only clean, semantic HTML code.
                DO NOT include:
                - No markdown code block markers (```)
            - No language identifiers
            - No explanations before or after the code
            """
            },
            {"role": "user", "content": html_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_css(self, html: str) -> str:
        """Generate CSS file based on HTML structure."""
        # Check for profile picture in temp/imgs folder
        profile_pic_exists = os.path.exists(os.path.join("temp", "imgs", "profile_pic.jpg"))
        
        profile_pic_section = """
2. Profile Picture Styling:
   - Set max-width: 200px
   - Set max-height: 200px
   - Create circular profile picture with border-radius: 50%
   - Add white border: 3px solid #ffffff
   - Use object-fit: cover to maintain aspect ratio
   - Position on the right side of the content
   - Add margin-left for spacing from text
   - Add subtle box shadow
   - Add responsive sizing for mobile devices""" if profile_pic_exists else ""

        css_prompt = f"""Create clean CSS for this HTML structure:

{html}

Style Requirements:
1. Text Styling:
   - All text must be left-aligned
   - Clear headers
   - Clean typography
   - Max-width: 600px for text blocks
   - Ensure text CONTRASTS with dark background

{profile_pic_section}

3. Colors and Visibility:
   - Text must be clearly visible (light color on dark, dark color on light)
   - Subtle hover effects for links
   - NO boxes or containers
   - Content directly on particles background

4. Spacing:
   - Generous margins between sections
   - Proper line height for readability
   - Comfortable padding where needed

5. Critical Requirements:
   - Style all HTML elements present in the code
   - Ensure navigation is centered and properly spaced
   - Make contact links clearly clickable
   - Keep particles visible behind content
   - NO background colors on content sections
   - Make profile picture container centered on page

6. Responsive Design:
   - Profile picture and content should scale down on mobile
   - Ensure proper spacing on all devices

Return ONLY the CSS code that matches this HTML structure without any explanations, comments, or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a CSS expert. Return only clean, efficient CSS code. Include specific sizing for profile pictures and ensure responsive design.
            DO NOT include:
            - No markdown code block markers (```)
            - No language identifiers
            - No explanations before or after the code
            """
            },
            {"role": "user", "content": css_prompt}
        ])

        # Add specific profile picture styles if they're missing from the LLM response
        css_content = response if isinstance(response, str) else response.get('content', '')
        
        if profile_pic_exists and ".profile-pic" not in css_content:
            profile_pic_css = """
/* Profile Picture Styles */
.profile-pic-container {
    width: 200px;
    height: 200px;
    margin: 2rem auto;
    overflow: hidden;
    border-radius: 50%;
    border: 3px solid #ffffff;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.profile-pic {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

@media (max-width: 768px) {
    .profile-pic-container {
        width: 150px;
        height: 150px;
        margin: 1.5rem auto;
    }
}
"""
            css_content += profile_pic_css

        return css_content

    async def _generate_js(self, html: str, css: str) -> str:
        """Generate JavaScript file based on HTML and CSS."""
        js_prompt = f"""Create JavaScript for this HTML and CSS:

HTML:
{html}

CSS:
{css}

Requirements:
1. Particles Background:
   - Initialize particles.js with an elegant theme
   - Ensure particles are visible but subtle
   - Include proper error handling

2. Text Animations:
   - Use GSAP for animations
   - Create fade-in animations for all main content elements
   - Include subtle movement (like slide up)
   - Use appropriate timing and easing
   - Maintain professional, smooth transitions
   - Define ALL animation configurations within this file
   - DO NOT reference external animation configurations

3. Error Handling:
   - Check if elements exist before animating
   - Graceful fallbacks
   - Console warnings for missing elements

4. Performance:
   - Initialize after DOM content loaded
   - Optimize animation performance
   - Ensure smooth interaction between particles and animations

Return ONLY the JavaScript code without any explanations, comments, or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a JavaScript expert who ensures:
- Dynamic, responsive animations
- Professional particle effects
- Smooth performance
- Proper error handling
Generate code that works with the provided HTML structure.

DO NOT include:
- No markdown code block markers (```)
- No language identifiers
- No explanations before or after the code"""
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

    async def _parse_resume(self, resume_content: str) -> Optional[Dict[str, Any]]:
        """Parse resume for both personal info and sections."""
        try:
            # First attempt - explicit extraction with more guidance
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
2. Current role, following these rules:
   - If they're a student: use "[Degree] Student at [University]"
   - If employed: use most recent "[Job Title] at [Company]"
   - Examples: 
     * "M.S. Computer Science Student at Stanford University"
     * "Software Engineer at Google"
     * "Data Science Intern at Figma"
3. Contact info (email, phone, LinkedIn)
4. Main section headers

Format EXACTLY like this:
name: John Smith
role: M.S. Computer Science Student at Stanford University
contact: email, phone, linkedin
sections: Education, Experience, Skills, Projects

Resume text:
{resume_content}"""}
            ])

            # Parse the response
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
            self.personal_info = {
                "name": info_dict.get('name', ''),
                "role": info_dict.get('role', ''),
                "contact": info_dict.get('contact', ''),
                "bio": bio_text.strip(),
                "sections": [s.strip() for s in info_dict.get('sections', '').split(',') if s.strip()] or 
                           ['Education', 'Experience', 'Skills', 'Projects']
            }

            # Verify we have all required fields
            missing_fields = []
            if not self.personal_info['name']:
                missing_fields.append('name')
            if not self.personal_info['role']:
                missing_fields.append('role')
            if not self.personal_info['contact']:
                missing_fields.append('contact')

            if missing_fields:
                print(f"Missing information: {', '.join(missing_fields)}")
                return None

            print(f"Successfully parsed resume information: {self.personal_info}")
            return self.personal_info

        except Exception as e:
            print(f"Resume parsing error: {str(e)}")
            return None

    async def _parse_resume_sections(self, resume_content: str) -> List[str]:
        """Extract major section headers from resume."""
        section_prompt = f"""Extract the major section headers from this resume. 
Return ONLY the section names in a comma-separated list.
Common sections include: Education, Experience, Skills, Projects, Publications, etc.
Do not include small subsections or individual entries.

Resume:
{resume_content}"""

        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": "Extract main section headers from resumes. Return only a comma-separated list."
                },
                {"role": "user", "content": section_prompt}
            ])

            # Get sections from response
            content = response['content'] if isinstance(response, dict) else response
            sections = [s.strip() for s in content.split(',')]
            self.resume_sections = sections
            return sections

        except Exception as e:
            print(f"Section parsing error: {str(e)}")
            raise

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