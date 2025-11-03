"""LLM client with support for multiple providers."""

import base64
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import httpx
from openai import AsyncOpenAI

from .config import config
from .schemas import AgentAction
from .utils.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    async def generate_with_vision(
        self,
        messages: List[Dict[str, Any]],
        image_base64: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate response with vision input."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """Generate response from OpenAI."""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_with_vision(
        self,
        messages: List[Dict[str, Any]],
        image_base64: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate response with vision input."""
        # Add image to the last user message
        vision_messages = messages.copy()
        if vision_messages and vision_messages[-1]["role"] == "user":
            vision_messages[-1]["content"] = [
                {"type": "text", "text": vision_messages[-1]["content"]},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        
        return await self.generate(
            vision_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """Generate response from Ollama."""
        try:
            # Convert messages to Ollama format
            prompt = self._messages_to_prompt(messages)
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False,
                    "format": "json" if json_mode else None
                }
            )
            response.raise_for_status()
            
            return response.json()["response"]
        
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def generate_with_vision(
        self,
        messages: List[Dict[str, Any]],
        image_base64: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate response with vision input."""
        # Note: This requires a vision-capable model like llava
        try:
            prompt = self._messages_to_prompt(messages)
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_base64],
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            return response.json()["response"]
        
        except Exception as e:
            logger.error(f"Ollama vision generation failed: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """Convert OpenAI-style messages to single prompt."""
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)


class LLMClient:
    """Main LLM client that routes to appropriate provider."""
    
    def __init__(self):
        self.provider = self._create_provider()
        logger.info(f"Initialized LLM client with provider: {config.settings.llm_provider}")
    
    def _create_provider(self) -> LLMProvider:
        """Create the appropriate LLM provider."""
        if config.settings.llm_provider == "openai":
            if not config.settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return OpenAIProvider(
                api_key=config.settings.openai_api_key,
                model=config.settings.openai_model
            )
        
        elif config.settings.llm_provider == "ollama":
            return OllamaProvider()
        
        else:
            raise ValueError(f"Unsupported LLM provider: {config.settings.llm_provider}")
    
    async def generate_action(
        self,
        observation: str,
        goals: List[str],
        step_history: List[Dict[str, Any]],
        max_retries: int = 3
    ) -> Optional[AgentAction]:
        """Generate next action from observation."""
        messages = [
            {
                "role": "system",
                "content": self._get_executor_prompt(goals)
            },
            {
                "role": "user",
                "content": self._format_action_request(observation, goals, step_history)
            }
        ]
        
        for attempt in range(max_retries):
            try:
                response = await self.provider.generate(
                    messages,
                    temperature=0.3,  # Lower temperature for more consistent actions
                    max_tokens=500,
                    json_mode=True
                )
                
                # Parse and validate action
                action_data = json.loads(response)
                
                # Map to appropriate action class
                action_type = action_data.get("action")
                if action_type == "click":
                    from .schemas import ClickAction
                    return ClickAction(**action_data)
                elif action_type == "fill":
                    from .schemas import FillAction
                    return FillAction(**action_data)
                elif action_type == "goto":
                    from .schemas import GotoAction
                    return GotoAction(**action_data)
                elif action_type == "press":
                    from .schemas import PressAction
                    return PressAction(**action_data)
                elif action_type == "select":
                    from .schemas import SelectAction
                    return SelectAction(**action_data)
                elif action_type == "wait_for_selector":
                    from .schemas import WaitForSelectorAction
                    return WaitForSelectorAction(**action_data)
                elif action_type == "assert_url_includes":
                    from .schemas import AssertUrlIncludesAction
                    return AssertUrlIncludesAction(**action_data)
                elif action_type == "done":
                    from .schemas import DoneAction
                    return DoneAction(**action_data)
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    continue
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse action JSON (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    messages.append({
                        "role": "user",
                        "content": "Invalid JSON. Please provide a valid action in JSON format only."
                    })
            except Exception as e:
                logger.error(f"Failed to generate action: {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    raise
        
        return None
    
    async def analyze_with_vision(
        self,
        screenshot_base64: str,
        question: str
    ) -> str:
        """Analyze screenshot with vision model."""
        messages = [
            {
                "role": "user",
                "content": question
            }
        ]
        
        return await self.provider.generate_with_vision(
            messages,
            screenshot_base64,
            temperature=0.5,
            max_tokens=500
        )
    
    def _get_executor_prompt(self, goals: List[str]) -> str:
        """Get the executor system prompt."""
        goals_section = "\n".join(f"- {goal}" for goal in goals) or "- Follow the user's instructions."
        
        return (
            "You are a browser automation agent. Analyze the current page and select the next action that moves the user closer to their goals while keeping the browser state stable.\n\n"
            f"Session goals provided by the user:\n{goals_section}\n\n"
            "You must respond with ONLY valid JSON matching one of these action schemas:\n\n"
            'Click: {"action": "click", "selector": "text=Continue"}\n'
            'Fill: {"action": "fill", "selector": "input[name=email]", "value": "user@example.com", "press_enter": false}\n'
            'Navigate: {"action": "goto", "url": "https://example.com/dashboard"}\n'
            'Press Key: {"action": "press", "key": "Enter"}\n'
            'Wait: {"action": "wait_for_selector", "selector": "text=Welcome", "timeout_ms": 10000}\n'
            'Assert URL: {"action": "assert_url_includes", "value": "/dashboard"}\n'
            'Complete: {"action": "done", "summary": "Login completed, dashboard opened."}\n\n'
            "Rules:\n"
            "1. Use semantic selectors when possible (text=, role=, label=)\n"
            "2. Be specific with selectors to avoid ambiguity\n"
            "3. Only navigate if explicitly needed for the goal\n"
            "4. Prefer clicking buttons over pressing Enter\n"
            "5. Wait for important elements after navigation\n"
            "6. Mark as done only when all goals are achieved\n"
            "7. Work in the same language the user provided when summarizing results\n"
            "8. NEVER include explanations - ONLY output the JSON action\n"
        )
    
    def _format_action_request(
        self,
        observation: str,
        goals: List[str],
        step_history: List[Dict[str, Any]]
    ) -> str:
        """Format the action request for the LLM."""
        request = f"""Current State:
{observation}

Goals to achieve:
{chr(10).join(f'- {goal}' for goal in goals)}

"""
        
        if step_history:
            request += "Recent actions:\n"
            for step in step_history[-5:]:  # Last 5 steps
                if step.get("action"):
                    request += f"- {step['action']['action']}: {step.get('result', 'pending')}\n"
        
        request += "\nWhat is the next action? Respond with JSON only."
        
        return request


# Global LLM client instance
llm_client = LLMClient()
