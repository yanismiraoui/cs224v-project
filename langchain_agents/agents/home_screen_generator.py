from custom_together_llm import TogetherLLM
from typing import Optional, Dict, Union, Any, List
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from dataclasses import dataclass
from datetime import datetime

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
            model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
            temperature=0.7,
            max_tokens=4000
        )
        self.personal_info = {}
        self.current_design = None
        self.profile_pic_path = "static/images/profile_pic.jpg"  # Default path to look for profile pic

    async def generate_home_screen(self, 
                                 user_input: str,
                                 resume_content: str = None) -> Union[Dict[str, str], str]:
        """Generate the home screen based on user input."""
        try:
            if not self.current_design:
                if resume_content and not self.personal_info:
                    parsed_info = await self._parse_resume(resume_content)
                    if parsed_info is None:
                        # Return indication that we need manual input
                        return {
                            'status': 'need_info',
                            'message': 'Could not extract all information from resume. Please provide manually.'
                        }
                
                self.current_design = await self._generate_initial_design(user_input)
                return self.current_design
            else:
                self.current_design = await self._update_design(user_input)
                return self.current_design

        except Exception as e:
            print(f"Generation error: {str(e)}")
            raise

    async def _generate_initial_design(self, user_input: str) -> str:
        """Generate website code using separate calls for HTML, CSS, and JS."""
        try:
            # Generate HTML first
            html_code = await self._generate_html()
            
            # Generate CSS based on HTML
            css_code = await self._generate_css(html_code)
            
            # Generate JS based on HTML and CSS
            js_code = await self._generate_js(html_code, css_code)

            # Format the response with labels outside code blocks
            formatted_response = f"""HTML Code:
{html_code.strip()}

CSS Code:
{css_code.strip()}

JavaScript Code:
{js_code.strip()}"""

            return formatted_response

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
        html_prompt = f"""Create a clean HTML file for a personal website with these requirements:

Content:
- Name: {self.personal_info.get('name')}
- Role: {self.personal_info.get('role')}
- Bio: {self.personal_info.get('bio')}
- Contact: {self.personal_info.get('contact')}

Structure:
1. Navigation bar with:
   - "About Me" (index.html)
   - Section links: {', '.join(self.personal_info.get('sections', []))}

2. Main content:
   - Name (h1)
   - Role (professional subtitle)
   - Bio paragraph
   - "Get in Touch" section with hyperlinked contact info

Requirements:
- Clean, semantic HTML
- No styling classes (minimal classes needed)
- Proper indentation
- Include particles-js container
- Link to external scripts (particles.js, gsap)

Return ONLY the HTML code."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an HTML expert. Return only clean, semantic HTML code."
            },
            {"role": "user", "content": html_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _generate_css(self, html: str) -> str:
        """Generate CSS file based on HTML structure."""
        css_prompt = f"""Create clean CSS for this HTML structure:

{html}

Style Requirements:
1. Text Styling:
   - All text must be left-aligned
   - Bold, clear headers
   - Clean typography
   - Max-width: 600px for text blocks
   - Ensure text CONTRASTS with dark background

2. Colors and Visibility:
   - Dark, elegant theme (#0a0a0a background)
   - Text must be clearly visible (light color on dark)
   - Subtle hover effects for links
   - NO boxes or containers
   - Content directly on particles background

3. Spacing:
   - Generous margins between sections
   - Proper line height for readability
   - Comfortable padding where needed

4. Critical Requirements:
   - Style all HTML elements present in the code
   - Ensure navigation is properly spaced
   - Make contact links clearly clickable
   - Keep particles visible behind content
   - NO background colors on content sections

Return ONLY the CSS code that matches this HTML structure."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a CSS expert who ensures:
- All content is visible and readable
- Styles match HTML structure exactly
- No conflicts with particles background
- Professional spacing and typography"""
            },
            {"role": "user", "content": css_prompt}
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
   - Initialize particles.js
   - Dark, elegant particle effect
   - Ensure particles are visible
   - Handle initialization errors

2. Animations:
   - Add animations ONLY for elements that exist in HTML
   - Smooth fade-in effects
   - Text reveal for appropriate elements
   - Respect existing styles
   - Don't override CSS positioning

3. Error Handling:
   - Check if elements exist before animating
   - Graceful fallbacks
   - Console warnings for missing elements
   - Clean error handling

4. Performance:
   - Efficient animations
   - No conflicts with particles
   - Smooth loading sequence
   - Proper event handling

Return ONLY JavaScript code that works with this specific HTML and CSS."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": """You are a JavaScript expert who ensures:
- Animations work with existing elements
- No conflicts with HTML/CSS
- Proper error handling
- Smooth performance"""
            },
            {"role": "user", "content": js_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    async def _update_design(self, feedback: str) -> str:
        """Update existing design based on user feedback."""
        update_prompt = f"""Update the existing website design based on this feedback:

User Feedback: "{feedback}"

Current Design:
{self.current_design}

Make the requested changes while maintaining all existing features and structure.
Return the complete updated code in three separate blocks."""

        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": """You are a web designer updating websites based on user feedback.
Always return complete HTML, CSS, and JavaScript code blocks.
Never return partial updates - include all existing code with your changes."""
                },
                {"role": "user", "content": update_prompt}
            ])

            content = response['content'] if isinstance(response, dict) else response
            
            # Extract all code blocks
            html = self._extract_code_block(content, 'html')
            css = self._extract_code_block(content, 'css')
            js = self._extract_code_block(content, 'javascript')

            # Ensure we have all components
            if not all([html, css, js]):
                print("Warning: Some code blocks were missing from the response")
                # Parse current_design for any missing blocks
                current_html = self._extract_code_block(self.current_design, 'html')
                current_css = self._extract_code_block(self.current_design, 'css')
                current_js = self._extract_code_block(self.current_design, 'javascript')
                
                html = html or current_html
                css = css or current_css
                js = js or current_js

            # Replace profile pic placeholder if available
            if self.profile_pic_path:
                html = html.replace('${self.profile_pic_path}', self.profile_pic_path)

            # Format the response with clear labels and code blocks
            formatted_response = f"""HTML Code:
```html
{html}
```

CSS Code:
```css
{css}
```

JavaScript Code:
```javascript
{js}
```"""

            return formatted_response

        except Exception as e:
            print(f"Design update error: {str(e)}")
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
            print("Raw Resume Parse Response:", info_text)  # Debug print
            
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

    def create_preview(self, html: str, css: str, js: str) -> str:
        """Create a combined preview version."""
        return f"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Preview</title>
    <script src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js'></script>
    <script src='https://cdn.jsdelivr.net/npm/particles.js@2.0.0/particles.min.js'></script>
    <style>{css}</style>
</head>
<body>
    {html}
    <script>{js}</script>
</body>
</html>""" 