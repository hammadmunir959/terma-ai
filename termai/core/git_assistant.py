"""Natural Language Git Assistant"""

from typing import Dict, Any, Optional, List
from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager
from .teaching import TeachingMode


class GitAssistant:
    """Natural language Git command assistant"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize Git assistant"""
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()
        self.display = DisplayManager()
        self.teaching = TeachingMode()
        self.executor = CommandExecutor()

    def process_git_request(self, request: str, execute: bool = False, explain: bool = False) -> Dict[str, Any]:
        """
        Process a natural language Git request
        
        Args:
            request: Natural language Git request
            execute: If True, execute the generated commands
            explain: If True, provide detailed explanations
            
        Returns:
            Dictionary with commands and results
        """
        git_prompt = self._get_git_prompt(request)
        
        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": self._get_git_system_prompt()},
                    {"role": "user", "content": git_prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            
            content = response.choices[0].message.content
            result = self._parse_git_response(content)
            result["original_request"] = request
            
            # Show commands
            commands = result.get("commands", [])
            explanations = result.get("explanations", [])
            
            if commands:
                self.display.show_commands(commands, explanations)
                
                # Explain if requested
                if explain:
                    for cmd, explanation in zip(commands, explanations):
                        self.display.console.print(f"\n[bold]📚 Explanation for:[/bold] [green]{cmd}[/green]")
                        self.display.console.print(f"[dim]{explanation}[/dim]")
                
                # Safety check
                safety_result = self.safety_checker.check_commands(commands)
                
                if safety_result.get("has_risky"):
                    self.display.show_risky_commands(safety_result["risky_commands"])
                    has_critical = any(c.get("risk_level") == "CRITICAL" for c in safety_result.get("risky_commands", []))
                    
                    if not self.display.confirm_risky_execution(
                        len(safety_result["risky_commands"]),
                        len(commands),
                        has_critical
                    ):
                        result["executed"] = False
                        result["cancelled"] = True
                        return result
                
                # Execute if requested
                if execute:
                    if not self.display.confirm_execution(len(commands)):
                        result["executed"] = False
                        result["cancelled"] = True
                        return result
                    
                    self.display.show_execution_start()
                    execution_result = self.executor.execute_commands(commands, explanations)
                    result["execution_result"] = execution_result
                    result["executed"] = True
                    result["success"] = execution_result.get("all_successful", False)
                    
                    self.display.show_execution_results(execution_result["results"], verbose=False)
                else:
                    result["executed"] = False
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to process Git request: {str(e)}",
                "original_request": request
            }

    def _get_git_system_prompt(self) -> str:
        """Get system prompt for Git assistant"""
        return """You are a Git expert assistant. Convert natural language Git requests into safe, correct Git commands.

Common Git operations:
- Commit: git commit -m "message"
- Add files: git add <files>
- Status: git status
- Log: git log, git log --oneline
- Branch: git branch, git checkout, git switch
- Merge: git merge <branch>
- Push/Pull: git push, git pull
- Undo: git reset, git revert, git restore
- Stash: git stash, git stash pop
- Remote: git remote, git remote add

Return as JSON:
{
  "commands": ["git command1", "git command2"],
  "explanations": ["explanation1", "explanation2"],
  "warning": "optional warning if operation is destructive"
}

Guidelines:
- Use safe Git commands
- Warn about destructive operations (force push, hard reset)
- Provide clear explanations
- Break complex operations into steps"""

    def _get_git_prompt(self, request: str) -> str:
        """Get user prompt for Git request"""
        return f"""Convert this Git request into commands: "{request}"

Return only valid JSON with commands and explanations."""

    def _parse_git_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into Git command structure"""
        import json
        import re
        
        try:
            content = content.strip()
            
            # Extract JSON
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            result = json.loads(content)
            
            # Validate
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            commands = result.get("commands", [])
            explanations = result.get("explanations", [])
            
            # Ensure explanations match commands
            while len(explanations) < len(commands):
                explanations.append("Execute this Git command")
            while len(commands) < len(explanations):
                commands.pop()
            
            return {
                "commands": commands,
                "explanations": explanations,
                "warning": result.get("warning", "")
            }
            
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from AI",
                "commands": [],
                "explanations": []
            }
        except Exception as e:
            return {
                "error": f"Failed to parse response: {str(e)}",
                "commands": [],
                "explanations": []
            }
