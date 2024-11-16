from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from tools import generate_website_content, optimize_profile, publish_to_github_pages
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, Dict, Any, List
from custom_together_llm import TogetherLLM
import logging
from datetime import datetime
from pathlib import Path



prompt = ChatPromptTemplate.from_messages([
  ("system", """
Here are the tools available to you:

<tools>
{tools}
</tools>

You are an advanced AI assistant called RecruiTree specializing in job applications and professional online presence. 
Your primary functions include helping users create professional websites and optimize their GitHub profiles. 
Your goal is to provide helpful, accurate, and complete responses to user queries, while being proactive in suggesting next steps.

The names of these tools are:

<tool_names>
{tool_names}
</tool_names>

Instructions:

1. Carefully analyze the user's input to understand their request or question.

2. If you need clarification or additional information, ask the user for more information without using any tools and directly ask the user using the "Final Answer" tool.

3. If you have enough information to proceed, determine whether you need to use a tool or can provide a direct answer.

4. If a tool is needed, use the following JSON format to specify the tool and its input:

Action:
```
{{
   "action": "TOOL_NAME", 
   "action_input": "TOOL_INPUT"
}}
```

Replace TOOL_NAME with one of the tool names from the <tool_names> list, and TOOL_INPUT with the appropriate input for that tool.

5. After using a tool, analyze its output and determine if additional steps are needed.

6. When you have all the necessary information, formulate your final answer using this JSON format:

Action:
```
{{
    "action": "Final Answer", 
    "action_input": "Your detailed response here"
}}
```

7. In your final answer, be sure to:
   - Provide a complete and accurate response to the user's query
   - Include any relevant tool outputs if they would be helpful to the user
   - Suggest proactive next steps the user can take

8. If the user asks for website content, include the full, correctly formatted website code in your final answer. This is very important.

Before providing your final answer, break down your thought process inside <analysis> tags. Consider the user's request, available tools, and potential next steps.

Example of the analysis and response structure:

<analysis>
1. Key elements of user's request: [List key points]
2. Relevant tools: [List potentially useful tools]
3. Clarification needed?: [Yes/No, explain if yes]
4. Tool usage plan: [Specify tool(s) to use or explain why no tool is needed]
5. Tool input planning (if applicable): [Draft the input for chosen tool(s)]
6. Analysis of tool output (if applicable): [Summarize key findings]
7. Response structure: [Outline the main points to cover in the final answer]
8. Next steps for user: [List proactive suggestions]
</analysis>

Action:
```
{{
    "action": "TOOL_NAME_OR_FINAL_ANSWER", 
 "action_input": "TOOL_INPUT_OR_FINAL_RESPONSE"
}}
```

Remember to always respond with a valid JSON blob containing a single action, either using a tool or providing the final answer. 
Do not mention tools names but instead mention what you can do with the tools.
If you don't need to use tools or lack sufficient information, respond directly with a final answer. 
Be thorough in your responses and always aim to provide value to the user in their job application process.
If the user asks for a website, include the full, correctly formatted website code in your final answer. This is very important.
   """),
("placeholder", "{chat_history}"),
("human", """{input}

{agent_scratchpad}
 (reminder to respond in a JSON blob no matter what)"""),
])

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"agent_actions_{timestamp}.log"
    
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

class JobApplicationAgent:
    def __init__(self):
        """Initialize the job application agent with LangChain components."""
        setup_logging()  # Initialize logging
        self.llm = TogetherLLM(temperature=0.1)
        
        # Add action history attribute
        self.action_history: List[Dict[str, Any]] = []
        
        # Initialize tools with logging wrapper
        self.tools = [
            self._create_logging_tool(generate_website_content),
            self._create_logging_tool(optimize_profile),
            self._create_logging_tool(publish_to_github_pages)
        ]
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

        # Remove all files in temp folder for a fresh start
        for file in Path("temp").glob("*"):
            file.unlink()
    
    def _create_logging_tool(self, tool):
        """Wrap a tool with logging functionality."""
        original_func = tool.func
        
        def logged_func(*args, **kwargs):
            # Create log entry
            tool_parameters = tool.func.__code__.co_varnames[:tool.func.__code__.co_argcount]
            tool_input = {
                param: arg for param, arg in zip(tool_parameters, args)
            }
            tool_input.update(kwargs)
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool.name,
                "tool_input": tool_input
            }
            
            # Add to action history
            self.action_history.append(log_entry)
            
            # Call the original function
            return original_func(*args, **kwargs)
        
        tool.func = logged_func
        return tool
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Return the action history."""
        return self.action_history
    
    async def process(self, user_input: str, resume_content: Optional[str] = None) -> str:
      """Process user input and get agent response."""
      try:  
          combined_input = user_input
          if resume_content:
              combined_input = f"{user_input}\nResume Content: {resume_content}"
      
          result = await self.agent_executor.ainvoke({"input": combined_input})
          print("Raw agent response:", result)
          return result.get("output", str(result))
      except Exception as e:
          return f"Error: {str(e)}"
