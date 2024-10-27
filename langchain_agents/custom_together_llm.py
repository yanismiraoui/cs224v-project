from typing import Any, List, Mapping, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
import together

class TogetherLLM(LLM):
    """Custom LangChain LLM wrapper for Together AI."""
    
    model_name: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo" #"meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo" #"meta-llama/Llama-3.2-3B-Instruct-Turbo" #"meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    temperature: float = 0.1
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "together_ai"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the LLM call."""
        # Format the prompt for chat
        formatted_prompt = f"<human>: {prompt}\n<assistant>:"

        response = together.Complete.create(
            prompt=formatted_prompt,
            model=self.model_name,
            temperature=self.temperature,
            stop=stop or ["<human>", "</human>", "<assistant>", "</assistant>"]
        )
        output = response['choices'][0]['text'].strip()
        print("Output from TogetherLLM:", output)
        return output

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
        }
