from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from tools import generate_website_content, optimize_profile
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, Dict, Any, List
from custom_together_llm import TogetherLLM
import logging
from datetime import datetime
from pathlib import Path



prompt = ChatPromptTemplate.from_messages([
  ("system", """You are a job application assistant. You can help a user with creating a professional website and optimizing their LinkedIn or GitHub profile. 
   
Respond to the human as helpfully and accurately as possible. Be complete in your response and do not hesitate to ask for clarification if needed. 
Be proactive and suggest actions to the user for next steps.
   
You have access to the following tools:

{tools}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{{
  "action": "Final Answer",
  "action_input": "Final response to human"
}}

Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation
Make sure to use the tools to respond the full answer, to the user's question but if you are not able to use the tools or do not have enough information, respond directly. 
Do not call tools if you do not need to, just give the final answer directly.
If you need to ask for more information, do not call tools, just ask the user for more information using "Final Answer".
If the user asks for a website, make sure to respond with the full website content, not just an answer like "Website generated successfully", include the website code correctly formatted and insterted in the "Final Answer".
If useful for the user, include the output of the tool in the "Final Answer".
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
            self._create_logging_tool(optimize_profile)
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
