"""OpenRouter API client for LLM communication"""

import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
import yaml
from pathlib import Path
from dotenv import load_dotenv
from .api_setup import require_api_key, APIKeySetupError


class LLMClient:
    """Client for interacting with OpenRouter API"""

    def __init__(self, config_path: Optional[str] = None, preferences: Optional[Any] = None, require_key: bool = True):
        """
        Initialize the LLM client with configuration
        
        Args:
            config_path: Optional path to config file
            preferences: Optional preferences object
            require_key: If True, raise error if API key is missing (default: True)
        """
        # Load environment variables from .env file
        load_dotenv()
        self.config = self._load_config(config_path)
        self.preferences = preferences

        # Check for API key with helpful error messages
        if require_key:
            self.api_key = require_api_key()
        else:
            self.api_key = os.getenv("API_KEY") or os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                self.api_key = None
                self.client = None
                return

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.config.get("api_base", "https://openrouter.ai/api/v1")
        )

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "settings.yaml"

        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return default configuration
            return {
                "provider": "openrouter",
                "model": "x-ai/grok-4.1-fast:free",
                "temperature": 0.2,
                "max_tokens": 300,
                "api_base": "https://openrouter.ai/api/v1"
            }

    def generate_commands(self, user_input: str) -> Dict[str, Any]:
        """
        Convert natural language input to bash commands using LLM

        Args:
            user_input: Natural language description of desired action

        Returns:
            Dict containing commands and explanations
        """
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(user_input)

        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.get("temperature", 0.2),
                max_tokens=self.config.get("max_tokens", 300)
            )

            content = response.choices[0].message.content
            return self._parse_response(content)

        except Exception as e:
            return {
                "error": f"Failed to generate commands: {str(e)}",
                "commands": [],
                "explanations": []
            }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for command generation"""
        base_prompt = """You are a Linux command generator for Terma AI.

Your task is to convert user requests into SAFE bash commands that can be executed in a Linux terminal.

CRITICAL SAFETY RULES:
- NEVER generate destructive commands like 'rm -rf /', 'mkfs', 'dd if=/dev/zero'
- NEVER use 'sudo' or privilege escalation
- NEVER edit system files in /etc, /boot, /bin, /usr/bin
- NEVER modify permissions dangerously (chmod 777, chown root)
- Prefer safe alternatives and read-only operations
- Always use absolute paths when possible
- Suggest commands that are informative rather than destructive

Return your response as valid JSON with this exact structure:
{
  "commands": ["command1", "command2"],
  "explanations": ["explanation1", "explanation2"],
  "safe": true
}

Guidelines:
- Generate 1-5 commands maximum
- Each explanation should be 1 short sentence
- If the request is too dangerous, set "safe": false and provide safe alternatives
- Focus on common Linux tasks: file operations, searching, monitoring, text processing"""
        
        # Add preferences if available
        if self.preferences:
            prefs_text = self.preferences.get_system_prompt_addition()
            if prefs_text:
                base_prompt += f"\n\nUser Preferences:\n{prefs_text}"
        
        return base_prompt

    def _get_user_prompt(self, user_input: str) -> str:
        """Get the user prompt for command generation"""
        return f"""Convert this user request into safe bash commands: "{user_input}"

Return only valid JSON with commands and explanations."""

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        try:
            # Try to parse as JSON
            result = json.loads(content.strip())

            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")

            commands = result.get("commands", [])
            explanations = result.get("explanations", [])
            safe = result.get("safe", True)

            # Ensure commands and explanations have the same length
            if len(commands) != len(explanations):
                # Pad explanations if necessary
                while len(explanations) < len(commands):
                    explanations.append("Execute this command")
                while len(commands) < len(explanations):
                    commands.pop()

            return {
                "commands": commands,
                "explanations": explanations,
                "safe": safe,
                "error": None
            }

        except json.JSONDecodeError:
            # Fallback parsing for non-JSON responses
            return {
                "commands": [],
                "explanations": [],
                "safe": False,
                "error": f"Invalid JSON response: {content[:100]}..."
            }

    def test_connection(self) -> bool:
        """Test the connection to OpenRouter API"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False
