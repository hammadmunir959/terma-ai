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

    def generate_commands(self, user_input: str, working_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert natural language input to bash commands using LLM

        Args:
            user_input: Natural language description of desired action
            working_directory: Optional working directory to get file context from

        Returns:
            Dict containing commands and explanations
        """
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(user_input, working_directory)

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

    def _get_user_prompt(self, user_input: str, working_directory: Optional[str] = None) -> str:
        """Get the user prompt for command generation with file context"""
        base_prompt = f"""Convert this user request into safe bash commands: "{user_input}"
"""
        
        # Add file context if working directory is provided
        if working_directory:
            file_context = self._get_file_context(working_directory)
            if file_context:
                base_prompt += f"""
IMPORTANT: Available files in current directory:
{file_context}

CRITICAL: Use the EXACT filenames (including case) from the list above. 
- If user says "radmap.md" but file is "ROADMAP.md", use "ROADMAP.md"
- If user says "readme" but file is "README.md", use "README.md"
- Match filenames case-insensitively but use the EXACT case from the file list
- If the user mentions a file that doesn't exist exactly, use the closest match from the available files
"""
        
        base_prompt += "\nReturn only valid JSON with commands and explanations."
        return base_prompt
    
    def _get_file_context(self, directory: str, max_files: int = 20) -> str:
        """Get a list of files in the directory for context"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return ""
            
            files = []
            dirs = []
            
            for item in sorted(path.iterdir()):
                if item.is_file():
                    files.append(item.name)
                elif item.is_dir():
                    dirs.append(item.name + "/")
            
            # Combine and limit
            all_items = files + dirs
            if len(all_items) > max_files:
                all_items = all_items[:max_files]
                all_items.append(f"... and {len(files) + len(dirs) - max_files} more")
            
            if all_items:
                return ", ".join(all_items)
            return ""
        
        except Exception:
            return ""

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

    def analyze_query(self, user_query: str, working_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a user query to determine if it needs command execution or just a conversational response
        
        Args:
            user_query: The user's question or request
            working_directory: Optional working directory for context
            
        Returns:
            Dict with analysis result indicating if commands are needed
        """
        system_prompt = """You are an intelligent assistant that analyzes user queries to determine if they need command execution.

Analyze the query and determine:
1. Does this query require executing terminal commands? (e.g., "list files", "check disk usage", "show git status")
2. Or is this a general question that can be answered conversationally? (e.g., "what is git?", "how does ls work?", "explain bash")

Return your response as valid JSON:
{
  "needs_execution": true/false,
  "reason": "brief explanation of why execution is/isn't needed",
  "query_type": "command_request" | "question" | "explanation_request" | "conversational"
}

Examples:
- "list files in current directory" → needs_execution: true, query_type: "command_request"
- "what is git?" → needs_execution: false, query_type: "question"
- "how do I check disk usage?" → needs_execution: false, query_type: "explanation_request"
- "show me the contents of README.md" → needs_execution: true, query_type: "command_request"
- "hello" → needs_execution: false, query_type: "conversational"
"""

        user_prompt = f"""Analyze this user query: "{user_query}"

Determine if it needs command execution or can be answered conversationally."""

        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            content = response.choices[0].message.content
            return self._parse_analysis_response(content)

        except Exception as e:
            # Default to needing execution if analysis fails
            return {
                "needs_execution": True,
                "reason": f"Analysis failed: {str(e)}",
                "query_type": "command_request"
            }

    def generate_conversational_response(
        self, 
        user_query: str, 
        command_results: Optional[List[Dict[str, Any]]] = None,
        working_directory: Optional[str] = None
    ) -> str:
        """
        Generate a natural language response to a user query
        
        Args:
            user_query: The user's question or request
            command_results: Optional list of command execution results
            working_directory: Optional working directory for context
            
        Returns:
            Natural language response string
        """
        system_prompt = """You are a helpful Linux terminal assistant. Provide clear, friendly, and informative responses.

Guidelines:
- Be conversational and natural, like ChatGPT
- Explain things clearly without being overly technical
- If command results are provided, summarize them in a user-friendly way
- Answer questions about Linux, commands, and terminal usage
- Be concise but thorough
"""

        user_prompt = f"""User query: "{user_query}"
"""

        # Add command results if available
        if command_results:
            results_text = "\nCommand execution results:\n"
            for i, result in enumerate(command_results, 1):
                cmd = result.get("command", "")
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                success = result.get("success", False)
                
                results_text += f"\nCommand {i}: {cmd}\n"
                results_text += f"Success: {success}\n"
                if stdout:
                    results_text += f"Output: {stdout[:500]}\n"  # Limit output length
                if stderr:
                    results_text += f"Error: {stderr[:500]}\n"
            
            user_prompt += results_text
            user_prompt += "\n\nProvide a natural language summary of what happened and answer the user's query based on these results."
        else:
            user_prompt += "\n\nProvide a helpful conversational response to this query."

        # Add file context if available
        if working_directory:
            file_context = self._get_file_context(working_directory)
            if file_context:
                user_prompt += f"\n\nCurrent directory context: {file_context}"

        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Higher temperature for more natural responses
                max_tokens=800  # More tokens for conversational responses
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"I encountered an error while generating a response: {str(e)}"

    def _parse_analysis_response(self, content: str) -> Dict[str, Any]:
        """Parse the query analysis response"""
        try:
            result = json.loads(content.strip())
            return {
                "needs_execution": result.get("needs_execution", True),
                "reason": result.get("reason", ""),
                "query_type": result.get("query_type", "command_request")
            }
        except json.JSONDecodeError:
            # Try to extract information from text response
            content_lower = content.lower()
            needs_execution = any(keyword in content_lower for keyword in [
                "needs execution", "requires command", "execute", "run command"
            ])
            return {
                "needs_execution": needs_execution,
                "reason": "Parsed from text response",
                "query_type": "command_request" if needs_execution else "question"
            }
