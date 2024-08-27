import os
from typing import Optional, Dict, Any, Callable
from openai import OpenAI
from anthropic import Anthropic

class GPT:
    def __init__(self, provider: str, api_key: Optional[str] = None, generate_func: Optional[Callable[[str, Dict[str, Any]], str]] = None):
      self.provider = provider

      if generate_func is None and self.provider not in ["openai", "anthropic", "together"]:
        raise ValueError(f"Unsupported provider: {provider}")
      elif generate_func is not None:
        self.provider = provider
        self.api_key = api_key
        self.generate = generate_func
        return

      if api_key is None:
        api_key = os.getenv(f"{provider.upper()}_API_KEY")

      self.default_models = {
        "together": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20240620"
      }

      if provider == "together":
        self.client = OpenAI(
          api_key=api_key,
          base_url="https://api.together.xyz/v1"
        )
      elif provider == "openai":
        self.client = OpenAI(api_key=api_key)
      elif provider == "anthropic":
        self.client = Anthropic(api_key=api_key)
      else:
        raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, prompt: str, params: Dict[str, Any] = {}) -> str:
        if "model" not in params:
          params["model"] = self.default_models[self.provider]
        if self.provider in ["together", "openai"]:
          response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **params
          )
          return response.choices[0].message.content
        elif self.provider == "anthropic":
          response = self.client.messages.create(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            **params
          )
        return response.content[0].text
