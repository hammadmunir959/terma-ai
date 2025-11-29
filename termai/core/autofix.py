"""Auto-fix terminal errors using AI"""

from typing import Dict, Any, Optional, List
from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager
from .teaching import TeachingMode


class AutoFix:
    """Automatically fix terminal command errors"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize the auto-fix system"""
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()
        self.display = DisplayManager()
        self.teaching = TeachingMode()

    def analyze_error(self, command: str, stderr: str, stdout: str = "", return_code: int = 1) -> Dict[str, Any]:
        """
        Analyze a command error and suggest fixes
        
        Args:
            command: The command that failed
            stderr: Error output
            stdout: Standard output (if any)
            return_code: Return code from command
            
        Returns:
            Analysis with suggested fixes
        """
        error_analysis_prompt = f"""A command failed with an error. Analyze the error and suggest fixes.

Failed Command: {command}
Return Code: {return_code}
Error Output: {stderr}
Standard Output: {stdout}

Provide:
1. What went wrong (simple explanation)
2. Why it failed
3. Suggested fix commands (1-3 options)
4. Explanation of the fix

Return as JSON:
{{
  "error_summary": "Brief description of the error",
  "root_cause": "Why it failed",
  "fixes": [
    {{
      "command": "fix command",
      "explanation": "Why this fixes it",
      "confidence": "high|medium|low"
    }}
  ],
  "prevention": "How to avoid this in the future"
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a Linux error diagnosis and fixing assistant. Analyze errors and provide clear, safe fixes."},
                    {"role": "user", "content": error_analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            analysis = self._parse_analysis(content)
            analysis["original_command"] = command
            analysis["error_output"] = stderr
            analysis["return_code"] = return_code
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Failed to analyze error: {str(e)}",
                "original_command": command,
                "error_output": stderr
            }

    def fix_error(self, command: str, stderr: str, stdout: str = "", return_code: int = 1,
                  auto_execute: bool = False, teaching_mode: bool = False) -> Dict[str, Any]:
        """
        Fix a command error
        
        Args:
            command: The command that failed
            stderr: Error output
            stdout: Standard output
            return_code: Return code
            auto_execute: If True, automatically execute the fix
            teaching_mode: If True, provide detailed explanations
            
        Returns:
            Fix results
        """
        # Analyze the error
        analysis = self.analyze_error(command, stderr, stdout, return_code)
        
        if analysis.get("error"):
            return analysis
        
        # Display error analysis
        self.display.console.print(f"\n[bold red]❌ Command Failed:[/bold red] [yellow]{command}[/yellow]")
        self.display.console.print(f"[red]Error:[/red] {analysis.get('error_summary', 'Unknown error')}")
        
        if teaching_mode:
            self.display.console.print(f"\n[bold]📚 Root Cause:[/bold] {analysis.get('root_cause', 'Unknown')}")
        
        # Show suggested fixes
        fixes = analysis.get("fixes", [])
        if not fixes:
            self.display.console.print("[yellow]⚠️  No automatic fixes available[/yellow]")
            return analysis
        
        self.display.console.print(f"\n[bold green]🔧 Suggested Fixes:[/bold green]")
        
        for i, fix in enumerate(fixes, 1):
            confidence_icon = "🟢" if fix.get("confidence") == "high" else "🟡" if fix.get("confidence") == "medium" else "🔴"
            self.display.console.print(f"\n{confidence_icon} [bold]Fix {i}:[/bold] [green]{fix['command']}[/green]")
            self.display.console.print(f"   [dim]{fix.get('explanation', '')}[/dim]")
        
        if analysis.get("prevention"):
            self.display.console.print(f"\n[bold]💡 Prevention:[/bold] {analysis['prevention']}")
        
        # Execute fix if requested
        if auto_execute and fixes:
            best_fix = fixes[0]  # Use highest confidence fix
            fix_command = best_fix["command"]
            
            # Safety check
            safety_result = self.safety_checker.check_commands([fix_command])
            
            if safety_result.get("has_risky"):
                self.display.show_risky_commands(safety_result["risky_commands"])
                has_critical = any(c.get("risk_level") == "CRITICAL" for c in safety_result.get("risky_commands", []))
                
                if not self.display.confirm_risky_execution(1, 1, has_critical):
                    return {
                        "fix_suggested": True,
                        "fix_executed": False,
                        "reason": "User cancelled risky fix"
                    }
            
            # Execute the fix
            self.display.console.print(f"\n[bold]🚀 Executing fix:[/bold] [green]{fix_command}[/green]")
            executor = CommandExecutor()
            result = executor.execute_commands([fix_command], [best_fix.get("explanation", "Auto-fix")])
            
            if result["results"][0]["success"]:
                self.display.console.print("[green]✅ Fix executed successfully![/green]")
                return {
                    "fix_suggested": True,
                    "fix_executed": True,
                    "fix_command": fix_command,
                    "success": True
                }
            else:
                self.display.console.print("[red]❌ Fix failed. Try another suggestion.[/red]")
                return {
                    "fix_suggested": True,
                    "fix_executed": True,
                    "fix_command": fix_command,
                    "success": False,
                    "error": result["results"][0].get("stderr", "")
                }
        
        return {
            "fix_suggested": True,
            "fix_executed": False,
            "analysis": analysis
        }

    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into analysis structure"""
        import json
        import re
        
        try:
            # Try to extract JSON
            content = content.strip()
            
            # Find JSON block
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            analysis = json.loads(content)
            
            # Validate structure
            if not isinstance(analysis, dict):
                raise ValueError("Analysis is not a dictionary")
            
            # Ensure fixes array exists
            if "fixes" not in analysis:
                analysis["fixes"] = []
            
            return analysis
            
        except json.JSONDecodeError:
            # Fallback: try to extract information manually
            return {
                "error_summary": "Could not parse error analysis",
                "root_cause": "Unknown",
                "fixes": [],
                "prevention": ""
            }
        except Exception as e:
            return {
                "error": f"Failed to parse analysis: {str(e)}",
                "fixes": []
            }
