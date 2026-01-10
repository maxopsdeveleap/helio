"""
LLM client abstraction layer.
Supports multiple providers: Claude API (Anthropic), AWS Bedrock.
"""
import os
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    CLAUDE_API = "claude_api"
    AWS_BEDROCK = "aws_bedrock"


class LLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def extract_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate and parse JSON from a prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Parsed JSON as dictionary
        """
        pass


class ClaudeAPIClient(LLMClient):
    """Claude API client using Anthropic SDK"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (default: Claude 3.5 Sonnet)
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables or constructor")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Initialized Claude API client with model: {model}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024) -> str:
        """Generate text using Claude API"""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)

            # Extract text from response
            text = response.content[0].text
            logger.debug(f"Generated {len(text)} characters (used {response.usage.input_tokens} input + {response.usage.output_tokens} output tokens)")
            return text

        except Exception as e:
            logger.error(f"Claude API generation failed: {e}")
            raise

    def extract_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate and parse JSON using Claude API"""
        import re

        # Add JSON instruction to prompt if not already present
        if "json" not in prompt.lower():
            prompt = f"{prompt}\n\nRespond with valid JSON only, no additional text."

        text = self.generate(prompt, system_prompt, max_tokens=2048)

        # Try to parse JSON
        try:
            original_text = text
            text = text.strip()

            # Remove markdown code blocks if present
            if text.startswith("```"):
                # Extract content between ``` markers
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
                text = text.strip()

            # Try to find JSON in the response using proper bracket/brace counting
            json_text = None

            # First try to find JSON array
            if '[' in text:
                start_idx = text.find('[')
                bracket_count = 0
                for i in range(start_idx, len(text)):
                    if text[i] == '[':
                        bracket_count += 1
                    elif text[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_text = text[start_idx:i+1]
                            logger.debug(f"Found JSON array in response")
                            break

            # If no array found, try to find JSON object
            if not json_text and '{' in text:
                start_idx = text.find('{')
                brace_count = 0
                in_string = False
                escape_next = False

                for i in range(start_idx, len(text)):
                    char = text[i]

                    if escape_next:
                        escape_next = False
                        continue

                    if char == '\\':
                        escape_next = True
                        continue

                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue

                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_text = text[start_idx:i+1]
                                logger.debug(f"Found JSON object in response")
                                break

            # If still no JSON found, try parsing entire text
            if not json_text:
                json_text = text

            data = json.loads(json_text)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Response text: {original_text[:500]}")
            raise ValueError(f"LLM did not return valid JSON: {e}")


class BedrockClient(LLMClient):
    """AWS Bedrock client (placeholder for future implementation)"""

    def __init__(self, model: str = "amazon.nova-lite-v1:0"):
        """
        Initialize Bedrock client.

        Args:
            model: Model ID to use (e.g., amazon.nova-lite-v1:0, anthropic.claude-3-5-sonnet-20241022-v2:0)
        """
        raise NotImplementedError("Bedrock client not yet implemented. Use Claude API for now.")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024) -> str:
        raise NotImplementedError()

    def extract_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError()


def get_llm_client(provider: Optional[str] = None, **kwargs) -> LLMClient:
    """
    Factory function to get an LLM client.

    Args:
        provider: Provider name ('claude_api' or 'aws_bedrock'). Defaults to ANTHROPIC_API_KEY env var.
        **kwargs: Additional arguments passed to the client constructor

    Returns:
        LLM client instance

    Example:
        # Use Claude API (default)
        client = get_llm_client()

        # Use specific provider
        client = get_llm_client(provider='claude_api', model='claude-3-5-sonnet-20241022')
    """
    # Default to Claude API if ANTHROPIC_API_KEY is set
    if provider is None:
        if os.getenv('ANTHROPIC_API_KEY'):
            provider = LLMProvider.CLAUDE_API.value
        elif os.getenv('AWS_REGION'):
            provider = LLMProvider.AWS_BEDROCK.value
        else:
            raise ValueError("No LLM provider configured. Set ANTHROPIC_API_KEY or AWS credentials.")

    if provider == LLMProvider.CLAUDE_API.value:
        return ClaudeAPIClient(**kwargs)
    elif provider == LLMProvider.AWS_BEDROCK.value:
        return BedrockClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: {[p.value for p in LLMProvider]}")
