from custom_together_llm import TogetherLLM
from typing import Optional, Dict, Any, List
import json
from dataclasses import dataclass
from datetime import datetime
import os

@dataclass
class Conversation:
    """Store conversation history and design preferences."""
    timestamp: datetime
    user_input: str
    design_preferences: Dict[str, Any]
    generated_code: Optional[Dict[str, str]] = None

class HomeScreenGeneratorAgent:
    """Agent specifically designed for generating personal home screens."""
    
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
        self.resume_content = None
        self.section_html = {}

    async def generate_home_screen(self, 
                                 user_input: str,
                                 resume_content: str = None) -> str:
        """Generate the home screen based on user input."""
        try:
            # Store resume content if provided
            if resume_content:
                self.resume_content = resume_content

            # 1. First get sections from resume
            if self.resume_content:
                sections = await self._parse_resume_sections()
                if sections:
                    self.personal_info = {'sections': sections}
                    print(f"Successfully extracted sections: {sections}")
                    
                    # Now parse content for each section
                    section_content = await self._parse_resume()
                    if section_content:
                        self.personal_info.update(section_content)
                        print("Successfully extracted section content")
                    print(f"Personal info: {json.dumps(self.personal_info, indent=2)}")

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

            # If we have a valid response, validate and save the files
            if all([self.html, self.css, self.js]):
                # Validate visual design
                validation_result = await self._validate_visual_design()
                
                # Save files to temp folder
                temp_dir = "temp"
                os.makedirs(temp_dir, exist_ok=True)

                # Use _extract_code_block to clean the code before writing
                with open(os.path.join(temp_dir, "index.html"), "w") as f:
                    clean_html = self._extract_code_block(self.html, "html")
                    f.write(clean_html)
                
                with open(os.path.join(temp_dir, "style.css"), "w") as f:
                    clean_css = self._extract_code_block(self.css, "css")
                    f.write(clean_css)
                
                with open(os.path.join(temp_dir, "script.js"), "w") as f:
                    clean_js = self._extract_code_block(self.js, "js")
                    f.write(clean_js)

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

    async def _generate_education_html(self) -> str:
        """Generate HTML specifically for education section."""
        education_data = self.personal_info.get('section_content', {}).get('education', [])
        
        if not education_data:
            return ""

        education_prompt = f"""Create ONLY the education section HTML with these requirements:

Education Data:
{json.dumps(education_data, indent=2)}

Technical Requirements:
- Create section with id="education"
- Include h2 header "Education"
- Each education entry must:
  * Use div with class="education-entry"
  * Include data-institution attribute
  * Have left side (edu-left) with institution and degree
  * Have right side (edu-right) with GPA and dates attended
- Maintain consistent structure and alignment
- Use semantic HTML5 elements

Return ONLY the education section HTML."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an HTML expert. Return only the education section HTML."
            },
            {"role": "user", "content": education_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _combine_html_sections(self, main_html: str, section_html: Dict[str, str]) -> str:
        """Combine main HTML with section-specific HTML content."""
        combine_prompt = f"""Combine these HTML sections while maintaining structure and semantic meaning.

Main HTML Structure:
{main_html}

Section-specific HTML to integrate:
{json.dumps(section_html, indent=2)}

Requirements:
- Insert each section in the appropriate place in main content
- Maintain all section IDs and classes
- Preserve navigation links and structure
- Keep all attributes and data properties
- Ensure proper nesting of elements
- Maintain semantic HTML structure
- Keep proper indentation

Return ONLY the complete, combined HTML code."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are an HTML expert specializing in combining HTML sections.
                Return only clean, semantic HTML without conflicts.
                DO NOT include any markdown formatting or explanations."""
            },
            {"role": "user", "content": combine_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_html(self) -> str:
        """Generate HTML file."""
        # Check for profile picture
        profile_pic_exists = os.path.exists(os.path.join("temp", "imgs", "profile_pic.jpg"))
        
        profile_pic_section = ""
        if profile_pic_exists:
            profile_pic_section = """
            Profile Picture Requirements:
            - MUST be inside a div with class="name-and-pic-container"
            - The name-and-pic-container MUST contain both:
              * The h1 heading with the name
              * The profile picture img
            - Profile picture MUST have class="profile-pic"
            - Profile picture MUST be placed directly next to the name
            - Profile picture MUST use imgs/profile_pic.jpg as src
            - Add proper alt text for accessibility"""
        
        sections = self.personal_info.get('sections', [])
        nav_links = []
        for section in sections:
            section_id = section.lower().replace(" ", "-").replace("&", "and")
            nav_links.append(f'- "{section}" links to "#{section_id}"')

        # Generate main HTML structure
        main_html_prompt = f"""Create a clean HTML file for a personal website with these requirements:

Content:
- Name: {self.personal_info.get('name')}
- Bio: {self.personal_info.get('bio')}
- Contact: {self.personal_info.get('contact')}
{profile_pic_section}

Structure:
1. Navigation bar with:
   - Each nav item MUST be an <a> tag linking to section IDs
   - Use href="#{{section_id}}" format
   - Navigation links MUST follow this EXACT pattern:
      {chr(10).join(nav_links)}

2. Main content:
   - CRITICAL: If profile picture exists, wrap name and picture in div.name-and-pic-container
   - Profile picture MUST be next to the name, on the same line but on the left side of the page
   - Section header "About Me" (h2) with id="about-me"
   - Bio sentence
   - Section header "Get In Touch" (h2) with id="contact"
   - Each contact method on separate line

<!-- Add the particles-js container to ensure the background is always active -->
<div id="particles-js"></div>

Example name and picture structure:
<div class="name-and-pic-container">
    <h1>{self.personal_info.get('name')}</h1>
    <img src="imgs/profile_pic.jpg" alt="Profile picture" class="profile-pic">
</div>

Requirements:
- Clean, semantic HTML
- Proper indentation
- Include particles-js container
- Link to external scripts
- Include style.css and script.js references
- Add scroll-behavior: smooth
- Each section must have matching nav link ID

Return ONLY the base HTML structure."""

        main_html = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an HTML expert. Return only clean, semantic HTML code."
            },
            {"role": "user", "content": main_html_prompt}
        ])

        # Generate section-specific HTML
        section_html = {
            'education': await self._generate_education_html(),
            'experience': await self._generate_technical_experience_html(),
            # Add other section HTML generators as needed
            'skills': await self._generate_skills_html(),
            # 'experience': await self._generate_experience_html(),
        }

        # Combine all HTML
        combined_html = await self._combine_html_sections(
            main_html if isinstance(main_html, str) else main_html.get('content', ''),
            section_html
        )

        return combined_html

    async def _combine_css_sections(self, main_css: str, section_css: Dict[str, str]) -> str:
        """Combine main CSS with section-specific CSS styles."""
        combine_prompt = f"""Combine and optimize these CSS sections while maintaining specificity and avoiding conflicts.

Main CSS:
{main_css}

Section-specific CSS to integrate:
{json.dumps(section_css, indent=2)}

Requirements:
- Maintain specificity of selectors
- Remove any duplicate rules
- Organize related styles together
- Preserve all functionality
- Ensure responsive designs work together
- Keep consistent spacing patterns
- Maintain hover effects and transitions

Return ONLY the complete, combined CSS code."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a CSS expert specializing in combining and optimizing stylesheets.
                Return only clean, efficient CSS without duplicates or conflicts.
                DO NOT include any markdown formatting or explanations."""
            },
            {"role": "user", "content": combine_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_css(self, html: str) -> str:
        """Generate CSS file based on HTML structure."""
        profile_pic_exists = os.path.exists("imgs/profile_pic.jpg")

        profile_pic_section = """
Profile Picture and Name Layout:
1. .name-and-pic-container:
   - MUST use display: flex
   - align-items: center
   - gap: 2rem
   - margin-bottom: 2rem
   - justify-content: flex-start

2. .profile-pic:
   - width: 150px
   - height: 150px
   - border-radius: 50%
   - object-fit: cover
   - border: 3px solid var(--accent-color)
   - box-shadow: 0 0 20px rgba(0,0,0,0.3)
   - transition: transform 0.3s ease
   
3. .profile-pic:hover:
   - transform: scale(1.05)

4. h1 in .name-and-pic-container:
   - margin: 0
   - flex: 1""" if profile_pic_exists else ""

        main_css_prompt = f"""Create base CSS for this HTML structure:

{html}

Style Requirements:
1. Layout and Alignment:
   - Main container: max-width: 1200px, centered
   - Main body text should align to the same left edge
   - NO staggered or uneven text alignment
   - Name section should start well below navigation
   - CRITICAL: Name and profile picture MUST be side-by-side using flexbox

{profile_pic_section}

2. Name and Profile Layout:
   - MUST use .name-and-pic-container with flexbox
   - Name and profile picture MUST be vertically centered
   - Clear spacing between this container and sections below
   - Container should use flexbox for alignment

3. Critical Spacing:
   - Large margin after each section's content (margin-bottom: 4rem)
   - Significant space before each header (margin-top: 3rem)
   - Headers should have breathing room below (margin-bottom: 2rem)
   - Consistent paragraph spacing (margin-bottom: 1.5rem)
   - Keep spacing proportional across screen sizes

4. Critical Z-Index and Positioning:
   - #particles-js: position: fixed, width/height 100%, z-index: -1
   - Main content: position: relative, z-index: 1
   - Navigation: position: fixed, z-index: 2
   - Ensure background stays behind all content

5. Text Styling:
   - Base font size: 18px for regular text
   - Consistent heading sizes
   - Clean typography with good line height
   - Keep text readable against the dark background
   - Optional: slightly larger text (20px) on wider screens

6. Colors and Visibility:
   - Text must be clearly visible on dark background
   - Make sure the text is visible at all times
   - Subtle hover effects for links
   - Content directly on background

7. Responsive Design:
   - Content should maintain alignment on all screens
   - Stack name and profile picture on mobile (flex-direction: column)
   - Min content width: 800px on desktop
   - Maintain proportional spacing on all devices

8. **Ensure the #particles-js container covers the entire background and remains fixed**

Return ONLY the base CSS code."""

        main_css = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a CSS expert. Return only the CSS code wrapped in proper markdown code blocks.
CRITICAL: Your response must start with ```css and end with ``` 
Do not include any other text or explanations."""
            },
            {"role": "user", "content": main_css_prompt}
        ])

        # Generate section-specific CSS
        section_css = {
            'education': await self._generate_education_css(),
            'experience': await self._generate_technical_experience_css(),
            # Add other section CSS generators as needed
            'skills': await self._generate_skills_css(),
            # 'experience': await self._generate_experience_css(),
        }

        # Combine all CSS
        combined_css = await self._combine_css_sections(
            main_css if isinstance(main_css, str) else main_css.get('content', ''),
            section_css
        )

        return combined_css

    async def _generate_education_css(self) -> str:
        """Generate CSS specifically for education section."""
        education_css_prompt = """Create CSS for the education section with these requirements:

Style Requirements:
1. Layout:
    - Each education entry should be a grid with two columns
    - Left column: Institution and degree info
    - Right column: Dates, GPA, Courses, etc
    - Add proper spacing between entries

2. Typography:
    - Institution name should be prominent and bold
    - Degree details slightly smaller but clear

3. Visual Effects:
    - Subtle hover effect on each entry
    - Hover effect should not be the same color as the text.
    - Smooth transitions for any hover states
    - Optional border or separator between entries

4. Responsive Design:
    - Stack columns on mobile devices
    - Maintain readability at all screen sizes
    - Adjust spacing for smaller screens

Return ONLY the CSS code for the education section."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Return only the education section CSS."
            },
            {"role": "user", "content": education_css_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_navigation_css(self) -> str:
        """Generate CSS specifically for navigation section."""
        navigation_css_prompt = """Create CSS for the navigation section with these requirements:

Style Requirements:
1. Layout and Alignment:
    - Fixed position at top of page
    - Full-width dark background container
    - Use same container width as main content (1200px)
    - Include padding on left and right
    - Include padding between the top and bottom of the container

2. Critical Alignment:
    - Navigation items MUST align with page content below
    - First nav item MUST align with leftmost content
    - Use same padding/margin system as main container
    - Maintain consistent left alignment across all screen sizes

3. Visual Effects:
    - Subtle hover effects on links
    - Smooth transitions
    - Semi-transparent background
    - Optional subtle shadow

4. Z-Index and Positioning:
    - position: fixed
    - z-index: 2
    - width: 100%
    - top: 0

5. Responsive Design:
    - Keep left alignment on all screen sizes
    - Maintain same content margins as main container
    - Adjust padding on mobile while keeping alignment

Return ONLY the CSS code for the navigation section."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Return only the navigation section CSS."
            },
            {"role": "user", "content": navigation_css_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

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
   - **Initialize particles.js after the DOM content is fully loaded to ensure it always runs**

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
                "content": """You are a JavaScript expert. Return only the JavaScript code wrapped in proper markdown code blocks.
CRITICAL: Your response must start with ```js and end with ```
Do not include any other text or explanations."""
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
        """Parse resume content for each section."""
        try:
            sections = self.personal_info.get('sections', [])
            
            # First get basic info
            info_response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": """You are a resume parser. Extract information precisely as requested."""
                },
                {"role": "user", "content": f"""Extract these basic details from the resume:
1. Full name (usually at top)
2. Current role, following these rules:
   - If they're a student: use "[Degree] Student at [University]"
   - If employed: use most recent "[Job Title] at [Company]"
3. Contact info (email, phone, LinkedIn)
4. Create a one-line professional bio

Return ONLY in this JSON format:
{{
    "name": "string",
    "role": "string",
    "contact": {{
        "email": "string",
        "phone": "string",
        "linkedin": "string"
    }},
    "bio": "string"
}}

Resume text:
{self.resume_content}"""}
            ])

            # Parse the basic info response
            info_text = info_response['content'] if isinstance(info_response, dict) else info_response
            basic_info = json.loads(info_text)

            # Define section-specific schemas
            section_schemas = {
                "Education": """{
                    "degree": "string",
                    "institution": "string",
                    "location": "string",
                    "dates": "string",
                    "gpa": "string (optional)",
                    "achievements": ["string"]
                }""",
                "Experience": """{
                    "title": "string",
                    "company": "string",
                    "location": "string",
                    "dates": "string",
                    "achievements": ["string"]
                }""",
                "Skills": """{
                    "technical": ["string"],
                    "soft": ["string"],
                    "tools": ["string"],
                    "languages": ["string"]
                }""",
                "Projects": """{
                    "name": "string",
                    "description": "string",
                    "technologies": ["string"],
                    "link": "string (optional)",
                    "achievements": ["string"]
                }""",
                "Publications": """{
                    "title": "string",
                    "authors": ["string"],
                    "venue": "string",
                    "date": "string",
                    "link": "string (optional)",
                    "description": "string"
                }"""
            }

            # Now get content for each section
            section_content = {}
            for section in sections:
                # Get the appropriate schema or use a default one
                schema = section_schemas.get(section, """{
                    "title": "string",
                    "description": "string",
                    "details": ["string"]
                }""")

                section_response = await self.llm.ainvoke([
                    {
                        "role": "system",
                        "content": f"Extract content for the {section} section using the specified JSON schema. Return an array of entries."
                    },
                    {"role": "user", "content": f"""Find and extract all content from the {section} section.
Each entry should follow this schema:
{schema}

Return ONLY a JSON array of entries following this schema. Example:
[
    {{ entry1 following schema }},
    {{ entry2 following schema }}
]

Resume:
{self.resume_content}"""}
                ])
                
                content = section_response['content'] if isinstance(section_response, dict) else section_response
                try:
                    parsed_content = json.loads(content)
                    section_content[section.lower().replace(' ', '_')] = parsed_content
                except json.JSONDecodeError:
                    print(f"Failed to parse content for {section} section")
                    continue

            # Combine basic info with section content
            result = {
                **basic_info,
                'section_content': section_content
            }

            print(f"Parsed resume content: {json.dumps(result, indent=2)}")
            return result

        except Exception as e:
            print(f"Resume parsing error: {str(e)}")
            return None

    async def _parse_resume_sections(self) -> List[str]:
        """Extract major section headers from resume that best match Education, Experience, and Skills."""
        section_prompt = f"""Analyze the resume and identify sections that best match these categories:
- Education (e.g., "Academic Background", "Educational History", "Degrees")
- Experience (e.g., "Work Experience", "Professional Experience", "Employment History", "Internships")
- Skills (e.g., "Technical Skills", "Core Competencies", "Expertise", "Technologies")

For each category, find the section that best matches it in the resume.
Return ONLY these matched section names in a comma-separated list, in the order they appear.
Skip any categories that don't have a good match in the resume.

Example response: "Educational Background, Professional Experience, Technical Skills"

Resume:
{self.resume_content}"""

        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": """You are an expert at analyzing resume sections.
Find the sections that best match Education, Experience, and Skills.
Return only a comma-separated list of the matched section names."""
                },
                {"role": "user", "content": section_prompt}
            ])

            # Get sections from response
            content = response['content'] if isinstance(response, dict) else response
            sections = [s.strip() for s in content.split(',')]
            
            # Map similar section names to standard ones
            section_mapping = {
                'education': 'Education',
                'experience': 'Experience',
                'skills': 'Skills'
            }
            
            # Standardize section names while preserving order
            standardized_sections = []
            for section in sections:
                section_lower = section.lower()
                for key, standard_name in section_mapping.items():
                    if key in section_lower:
                        standardized_sections.append(standard_name)
                        break
            
            print(f"Found sections: {sections}")
            print(f"Standardized to: {standardized_sections}")
            
            self.resume_sections = standardized_sections
            return standardized_sections

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
            
            # If no start marker found, treat entire text as code
            if start == -1:
                return text.strip()
            
            end = text.find("```", start)
            
            # If no end marker found, use rest of text
            if end == -1:
                return text[start:].strip()
            
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

    async def _generate_technical_experience_html(self) -> str:
        """Generate HTML specifically for technical experience section."""
        experience_data = await self._find_experience_section()
        
        if not experience_data:
            print("No technical experience data found!")
            return ""

        experience_prompt = f"""Create ONLY the technical experience section HTML with these requirements:

Technical Requirements:
1. Structure:
   - Section with id="technical-experience"
   - h2 header "Technical Experience"
   - Each experience entry MUST be wrapped in:
     * div class="experience-entry card"
     * Add proper card structure and padding
   - Each entry must include:
     * Company name as h3
     * Role title in italics
     * Dates right-aligned
     * Achievement list

2. Format Example:
   <section id="technical-experience">
     <h2>Technical Experience</h2>
     <div class="experience-entry card">
       <h3>Company Name</h3>
       <div class="role-date-line">
         <em>Role Title</em>
         <span class="dates">Date Range</span>
       </div>
       <ul>
         <li>Achievement details...</li>
       </ul>
     </div>
   </section>

Experience Data:
{json.dumps(experience_data, indent=2)}

Return ONLY the technical experience section HTML."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an HTML expert. Return only the technical experience section HTML."
            },
            {"role": "user", "content": experience_prompt}
        ])

        html_content = response if isinstance(response, str) else response.get('content', '')
        # Store the generated HTML
        self.section_html['technical_experience'] = html_content
        print("Saved technical experience HTML to section_html")
        return html_content

    async def _generate_technical_experience_css(self) -> str:
        """Generate CSS specifically for technical experience section."""
        # Get the stored HTML
        tech_exp_html = self.section_html.get('technical_experience', '')
        if not tech_exp_html:
            print("No technical experience HTML found!")
            return ""

        experience_css_prompt = f"""Given this EXACT technical experience HTML structure:

{tech_exp_html}

Create CSS that achieves these style requirements:
1. Card Layout:
   - .experience-entry.card:
     * Must have visible background color using var(--card-bg)
     * Must have rounded corners using var(--card-radius)
     * Must have padding using var(--card-padding)
     * Must have margin-bottom: 2rem
     * Must have visible box-shadow
     * Must have smooth transition
     * Must have border: 1px solid rgba(255,255,255,0.1)
   - .experience-entry.card:hover:
     * Must have slight scale transform
     * Must have enhanced shadow

2. Inner Layout:
   - Match the HTML structure exactly
   - Style all elements present in the HTML
   - Ensure proper spacing between all elements
   - Maintain hierarchy of information

3. Typography:
   - Style each heading and text element found in the HTML
   - Maintain proper visual hierarchy
   - Ensure readability

4. Critical Requirements:
   - CSS must match HTML classes exactly
   - Cards MUST be visibly distinct from background
   - All content must be properly spaced
   - Maintain consistent styling across all entries

Return ONLY the CSS code needed for this exact HTML structure."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Return only the CSS code that matches the provided HTML structure exactly."
            },
            {"role": "user", "content": experience_css_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_technical_experience_js(self) -> str:
        """Generate JavaScript specifically for technical experience section."""
        # First check if we have experience data
        experience_data = await self._find_experience_section()
        
        if not experience_data:
            print("No technical experience data found for JS!")
            return ""

        experience_js_prompt = """Create JavaScript for the technical experience section with these requirements:

Functionality Requirements:
1. Interactive Features:
    - Smooth scroll to section when nav link clicked
    - Optional expand/collapse for long achievement lists
    - Hover effects and animations
    - Optional filtering or sorting capabilities

2. Animation Effects:
    - Fade in entries on scroll
    - Smooth transitions for any interactive elements
    - Optional progressive loading of entries
    - Subtle hover animations

3. Utility Functions:
    - Handle any dynamic content loading
    - Manage responsive behaviors
    - Optional search/filter functionality
    - Event listeners for interactive elements

4. Performance:
    - Efficient event handling
    - Debounced scroll listeners
    - Optimized animations
    - Clean, modular code structure

Return ONLY the JavaScript code for the technical experience section."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a JavaScript expert. Return only the technical experience section JavaScript."
            },
            {"role": "user", "content": experience_js_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '') 

    async def _find_experience_section(self) -> List[Dict]:
        """Find the most relevant experience section from personal info."""
        section_prompt = """Among these sections from a resume, identify which contains technical/professional work experience.
Return ONLY the exact key name that best matches job experience (e.g., 'technical_experience', 'experience', 'work_experience').
If multiple relevant sections exist, return the most specific one.

Available sections:
{sections}

Example matches:
- "experience"
- "technical_experience"
- "work_experience"
- "professional_experience"
"""

        sections = self.personal_info.get('section_content', {})
        
        # Debug log available sections
        print(f"Available sections: {list(sections.keys())}")

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "Identify the most relevant experience section key. Return only the key name."
            },
            {"role": "user", "content": section_prompt.format(sections=json.dumps(list(sections.keys()), indent=2))}
        ])

        section_key = response if isinstance(response, str) else response.get('content', '')
        section_key = section_key.strip().lower()
        
        # Debug log selected section
        print(f"Selected experience section key: {section_key}")
        
        return sections.get(section_key, [])

    async def _generate_skills_html(self) -> str:
        """Generate HTML specifically for skills section."""
        skills_data = self.personal_info.get('section_content', {}).get('skills', [])
        
        if not skills_data:
            print("No skills data found!")
            return ""

        skills_prompt = f"""Create ONLY the skills section HTML with these requirements:

Skills Data:
{json.dumps(skills_data, indent=2)}

Technical Requirements:
1. Structure:
   - Section with id="skills"
   - h2 header "Skills"
   - Container div with class="skills-grid"
   - For each skill category (technical, soft, tools, etc):
     * ONLY create sections for categories that have content
     * SKIP any empty categories or categories with no skills
     * For non-empty categories:
       - div with class="skill-category"
       - h3 with category name
       - div with class="skill-items"
       - Each skill in a span with class="skill-tag"

2. Format Example:
   <section id="skills">
     <h2>Skills</h2>
     <div class="skills-grid">
       <!-- Only include if technical skills exist -->
       <div class="skill-category">
         <h3>Technical Skills</h3>
         <div class="skill-items">
           <span class="skill-tag">Python</span>
           <span class="skill-tag">JavaScript</span>
         </div>
       </div>
     </div>
   </section>

3. Critical Requirements:
   - DO NOT generate HTML for empty categories
   - DO NOT include categories with no skills
   - Only create sections for categories that have actual content
   - Maintain clean, semantic HTML structure

Return ONLY the skills section HTML."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are an HTML expert. Return only the skills section HTML.
CRITICAL: Skip any empty categories. Only generate HTML for categories that have actual skills listed."""
            },
            {"role": "user", "content": skills_prompt}
        ])

        html_content = response if isinstance(response, str) else response.get('content', '')
        self.section_html['skills'] = html_content
        return html_content

    async def _generate_skills_css(self) -> str:
        """Generate CSS specifically for skills section."""
        # Get the stored HTML
        skills_html = self.section_html.get('skills', '')
        if not skills_html:
            print("No skills HTML found!")
            return ""

        skills_css_prompt = f"""Given this EXACT skills section HTML structure:

{skills_html}

Create CSS that achieves these style requirements:
1. Grid Layout:
   - Match the HTML structure exactly
   - Style the grid container to display skills horizontally
   - Ensure proper spacing between all elements
   - Make grid responsive to screen size

2. Skill Categories:
   - Style each category container found in the HTML
   - Add visual separation between categories
   - Maintain consistent spacing
   - Use subtle backgrounds or borders

3. Skill Tags:
   - Style individual skill tags to appear side-by-side
   - Add visual distinction to each tag
   - Include subtle hover effects
   - Ensure proper spacing between tags

4. Typography:
   - Style each heading and text element found in the HTML
   - Maintain proper visual hierarchy
   - Ensure readability

5. Critical Requirements:
   - CSS must match HTML classes exactly
   - Skills must be clearly readable
   - Layout must be responsive
   - Maintain consistent styling across all categories

Return ONLY the CSS code needed for this exact HTML structure."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are a CSS expert. Return only the CSS code that matches the provided HTML structure exactly."
            },
            {"role": "user", "content": skills_css_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _validate_visual_design(self) -> Dict[str, Any]:
        """Validate color contrast and particles background implementation."""
        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": """You are an expert web developer specializing in visual design and accessibility.
Your task is to analyze code for contrast issues and particles.js implementation.
CRITICAL: You must return ONLY valid JSON matching this exact structure:
{
    "contrast_issues": [{"element": "string", "issue": "string", "fix": "string"}],
    "particles_issues": [{"issue": "string", "fix": "string"}],
    "is_valid": boolean,
    "summary": "string"
}"""
                },
                {"role": "user", "content": f"""Analyze this code for visual and particles.js issues:

HTML: {self.html}
CSS: {self.css}
JavaScript: {self.js}

Focus on:
1. Color contrast (white-on-white, low contrast, text readability)
2. Particles.js implementation (positioning, z-index, initialization without JSON file)
3. The content of the page is visible and not hidden by the particles background

Return analysis as JSON matching the structure specified in the system message."""}
            ])

            content = response if isinstance(response, str) else response.get('content', '')
            # Strip any markdown formatting that might be present
            content = content.strip().replace('```json', '').replace('```', '')
            validation_result = json.loads(content)
            
            # Apply fixes if there are issues
            if not validation_result['is_valid']:
                if validation_result['contrast_issues']:
                    print("Fixing contrast issues...")
                    await self._fix_contrast_issues(validation_result['contrast_issues'])
                
                if validation_result['particles_issues']:
                    print("Fixing particles issues...")
                    await self._fix_particles_issues(validation_result['particles_issues'])

            return validation_result

        except Exception as e:
            print(f"Error validating visual design: {str(e)}")
            return {
                "contrast_issues": [],
                "particles_issues": [],
                "is_valid": False,
                "summary": f"Validation failed with error: {str(e)}"
            }

    async def _fix_contrast_issues(self, issues: List[Dict[str, str]]) -> None:
        """Apply fixes for contrast issues."""
        for issue in issues:
            element = issue['element']
            fix = issue['fix']
            
            css_fix_prompt = f"""Update the CSS for {element} with this fix: {fix}

Current CSS:
{self.css}

Return ONLY the complete updated CSS."""

            try:
                response = await self.llm.ainvoke([
                    {
                        "role": "system",
                        "content": "You are a CSS expert. Apply the specified contrast fix and return the complete updated CSS."
                    },
                    {"role": "user", "content": css_fix_prompt}
                ])

                self.css = response if isinstance(response, str) else response.get('content', '')
                print(f"Applied contrast fix for {element}")

            except Exception as e:
                print(f"Error fixing contrast for {element}: {str(e)}")

    async def _fix_particles_issues(self, issues: List[Dict[str, str]]) -> None:
        """Apply fixes for particles.js implementation issues."""
        try:
            for issue in issues:
                fix = issue['fix']
                
                # Determine if fix is for HTML, CSS, or JS
                if 'z-index' in fix.lower() or 'position' in fix.lower():
                    # CSS fix
                    css_fix_prompt = f"""Update the CSS for particles.js with this fix: {fix}

Current CSS:
{self.css}

Return ONLY the complete updated CSS."""

                    response = await self.llm.ainvoke([
                        {
                            "role": "system",
                            "content": "You are a CSS expert. Apply the specified particles.js fix and return the complete updated CSS."
                        },
                        {"role": "user", "content": css_fix_prompt}
                    ])

                    self.css = response if isinstance(response, str) else response.get('content', '')
                    print("Applied particles CSS fix")

                elif 'initialization' in fix.lower() or 'config' in fix.lower():
                    # JavaScript fix
                    js_fix_prompt = f"""Update the JavaScript for particles.js with this fix: {fix}

Current JavaScript:
{self.js}

Return ONLY the complete updated JavaScript."""

                    response = await self.llm.ainvoke([
                        {
                            "role": "system",
                            "content": "You are a JavaScript expert. Apply the specified particles.js fix and return the complete updated JavaScript."
                        },
                        {"role": "user", "content": js_fix_prompt}
                    ])

                    self.js = response if isinstance(response, str) else response.get('content', '')
                    print("Applied particles JavaScript fix")

                else:
                    # HTML fix
                    html_fix_prompt = f"""Update the HTML for particles.js with this fix: {fix}

Current HTML:
{self.html}

Return ONLY the complete updated HTML."""

                    response = await self.llm.ainvoke([
                        {
                            "role": "system",
                            "content": "You are an HTML expert. Apply the specified particles.js fix and return the complete updated HTML."
                        },
                        {"role": "user", "content": html_fix_prompt}
                    ])

                    self.html = response if isinstance(response, str) else response.get('content', '')
                    print("Applied particles HTML fix")

        except Exception as e:
            print(f"Error fixing particles issue: {str(e)}")