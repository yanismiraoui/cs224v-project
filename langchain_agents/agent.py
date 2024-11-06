from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from tools import generate_website_content, optimize_profile
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional
from custom_together_llm import TogetherLLM



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
Make sure to respond the full answer, to the user's question. For example, if the user asks for a website, make sure to respond with the full website content, not just an answer like "Website generated successfully".
"""),
("placeholder", "{chat_history}"),
("human", """{input}

{agent_scratchpad}
 (reminder to respond in a JSON blob no matter what)"""),
])

class JobApplicationAgent:
    def __init__(self):
        """Initialize the job application agent with LangChain components."""
        self.llm = TogetherLLM(temperature=0.1)
        
        # Initialize tools
        self.tools = [
            generate_website_content,
            optimize_profile
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
