from typing import Any, List, Mapping, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
import together

class TogetherLLM(LLM):
    """Custom LangChain LLM wrapper for Together AI."""
    
    model_name: str = "togethercomputer/llama-2-70b-chat"
    temperature: float = 0.7
    max_tokens: int = 1024
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        together.api_key = api_key
    
    @property
    def _llm_type(self) -> str:
        return "together_ai"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the LLM call."""
        response = together.Complete.create(
            prompt=prompt,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop
        )
        return response['output']['choices'][0]['text']
