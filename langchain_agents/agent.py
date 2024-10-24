from langchain.agents import AgentExecutor, OpenAIFunctionsAgent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from .custom_together_llm import TogetherLLM
from .tools import WebsiteGeneratorTool, ProfileOptimizerTool

class JobApplicationAgent:
    def __init__(self, api_key: str):
        """Initialize the job application agent with LangChain components."""
        self.llm = TogetherLLM(api_key=api_key)
        self.tools = [
            WebsiteGeneratorTool(),
            ProfileOptimizerTool()
        ]
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.system_prompt = SystemMessage(
            content="""You are an AI assistant specialized in helping users optimize their job applications 
            and professional profiles. You can help with website generation and profile optimization.
            Provide clear, actionable advice and generate appropriate content when requested."""
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            self.system_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = OpenAIFunctionsAgent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )
    
    async def process(self, user_input: str) -> str:
        """Process user input and return agent response."""
        return await self.agent_executor.arun(input=user_input)
