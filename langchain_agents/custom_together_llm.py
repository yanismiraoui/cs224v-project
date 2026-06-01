from typing import Any, List, Mapping, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from together import Together
import os

try:
    from .config import get_secret
except ImportError:  # Allows running files directly from langchain_agents/
    from config import get_secret

class TogetherLLM(LLM):
    """Custom LangChain LLM wrapper for Together AI."""
    
    model_name: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    response_format: Optional[dict] = None
    
    def __init__(self, **kwargs):
        # Older call sites used ``model=...``; normalize it to the field LangChain
        # expects so those pages keep working.
        if "model" in kwargs and "model_name" not in kwargs:
            kwargs["model_name"] = kwargs.pop("model")
        super().__init__(**kwargs)
    
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

        api_key = get_secret('TOGETHER_API_KEY')
        if api_key is None:  # Defensive for type checkers; required=True raises first.
            raise ValueError("TOGETHER_API_KEY is required")
        os.environ['TOGETHER_API_KEY'] = api_key
        client = Together()

        request: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": prompt}],
            "stream": False,
            "temperature": self.temperature,
        }
        if self.max_tokens is not None:
            request["max_tokens"] = self.max_tokens
        if self.response_format is not None:
            request["response_format"] = self.response_format

        response = client.chat.completions.create(**request)
        output = response.choices[0].message.content
        return output

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
        }
