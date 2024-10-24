from typing import Dict, List, Optional
import together
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, api_key: str, model: str = "togethercomputer/llama-2-70b-chat"):
        """Initialize base agent with Together AI configuration.
        
        Args:
            api_key: Together AI API key
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model
        together.api_key = api_key
        
    async def generate_response(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response using Together AI.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            
        Returns:
            str: Generated response
        """
        response = together.Complete.create(
            prompt=prompt,
            model=self.model,
            temperature=temperature,
            max_tokens=1024
        )
        return response['output']['choices'][0]['text']
    
    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute agent's main functionality."""
        pass
    
    def _create_system_prompt(self, role: str) -> str:
        """Create system prompt for the agent.
        
        Args:
            role: Role description for the agent
            
        Returns:
            str: Formatted system prompt
        """
        return f"""You are an AI assistant specialized in {role}. 
        You will help users optimize their professional profiles and job applications.
        Provide clear, actionable advice and generate content when requested."""
