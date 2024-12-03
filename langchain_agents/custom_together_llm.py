from typing import Any, List, Mapping, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from together import Together
import os
import toml

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
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the LLM call."""

        # Read API key from secrets.toml
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secrets.toml')
        secrets = toml.load(secrets_path)
        os.environ['TOGETHER_API_KEY'] = secrets['TOGETHER_API_KEY']
        client = Together()

        # Format the prompt for chat
        print("Prompt: ", prompt)
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": prompt}
            ],
            stream=False,
            response_format={"type": "json_object"},
            temperature=self.temperature,
        )
        output = response.choices[0].message.content
        print("Output: ", output)
        return output

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
        }
