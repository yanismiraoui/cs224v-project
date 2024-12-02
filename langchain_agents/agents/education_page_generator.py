from custom_together_llm import TogetherLLM
from typing import Optional, Dict, Union, Any, List
import os
import json

class EducationPageGenerator:
    """Agent specifically designed for generating education pages."""
    
    def __init__(self):
        self.llm = TogetherLLM(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            temperature=0,
        )
        self.education_info = {}
        self.html = None
        self.css = None
        self.js = None

    async def generate_education_page(self, 
                                    resume_content: str = None,
                                    user_input: str = None) -> str:
        """Generate the education page based on resume content and user input."""
        try:
            # 1. Parse education information from resume
            if resume_content:
                parsed_info = await self._parse_education_info(resume_content)
                if parsed_info:
                    self.education_info = parsed_info
                    print("Successfully extracted education info from resume")

            # 2. Parse any additional user input
            if user_input:
                user_info = await self._parse_user_input(user_input)
                if user_info:
                    self.education_info.update(user_info)
                    print(f"Updated education information from user input")

            # 3. Generate or update design
            if not any([self.html, self.css, self.js]):
                await self._generate_initial_design()
            else:
                print("Updating design...")
                await self._update_design(user_input)

            # 4. Save the files
            if all([self.html, self.css, self.js]):
                temp_dir = "temp"
                os.makedirs(temp_dir, exist_ok=True)

                with open(os.path.join(temp_dir, "education.html"), "w") as f:
                    f.write(self.html.strip())
                
                # Only update CSS if it's different from existing
                if not os.path.exists(os.path.join(temp_dir, "style.css")):
                    with open(os.path.join(temp_dir, "style.css"), "w") as f:
                        f.write(self.css.strip())
                
                with open(os.path.join(temp_dir, "education.js"), "w") as f:
                    f.write(self.js.strip())
                
                return "Education page has been generated successfully!"
            else:
                return "Failed to generate all required components."

        except Exception as e:
            print(f"Generation error: {str(e)}")
            return f"Error generating education page: {str(e)}"

    async def _parse_education_info(self, resume_content: str) -> Dict[str, Any]:
        """Extract education information from resume."""
        try:
            prompt = f"""Extract detailed education information from this resume.
Include:
- Degrees (with majors/concentrations)
- Universities/Schools
- Graduation dates
- GPA (if mentioned)
- Relevant coursework
- Academic achievements
- Research projects

Format as JSON with these keys:
- institutions: list of objects with (name, location, degree, major, dates, gpa)
- coursework: list of relevant courses
- achievements: list of academic achievements
- projects: list of academic projects

Resume:
{resume_content}"""

            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": "You are an expert at extracting education information from resumes. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ])

            content = response if isinstance(response, str) else response.get('content', '')
            return json.loads(content)

        except Exception as e:
            print(f"Error parsing education info: {str(e)}")
            return {}

    async def _generate_initial_design(self) -> None:
        """Generate website code for education page."""
        try:
            self.html = await self._generate_html()
            self.css = await self._generate_css(self.html)
            self.js = await self._generate_js(self.html, self.css)

        except Exception as e:
            print(f"Design generation error: {str(e)}")
            raise

    async def _generate_html(self) -> str:
        """Generate HTML for education page."""
        html_prompt = f"""Create a clean HTML file for an education page with these requirements:

Content:
{json.dumps(self.education_info, indent=2)}

Structure:
1. Navigation bar (same as index.html)
2. Main content:
   - Each institution in a separate section
   - Degree and major prominently displayed
   - Dates and GPA in smaller text
   - Coursework in a grid or multi-column layout
   - Achievements in a list format
   - Academic projects with descriptions

Requirements:
- Clean, semantic HTML
- Proper heading hierarchy
- Consistent structure with index.html
- Link to style.css and education.js
- Include particles-js container

Return ONLY the HTML code without any explanations or markdown formatting."""

        response = await self.llm.ainvoke([
            {
                "role": "system",
                "content": "You are an HTML expert. Return only clean HTML code without any markdown or explanations."
            },
            {"role": "user", "content": html_prompt}
        ])

        return response if isinstance(response, str) else response.get('content', '')

    # ... Add _generate_css, _generate_js, _update_design methods similar to HomeScreenGenerator ...
    # ... Add _clean_code_block and other helper methods as needed ... 