"""System troubleshooting agent"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from .llm import LLMClient
from .executor import CommandExecutor
from .display import DisplayManager


class TroubleshootingAgent:
    """Interactive system troubleshooting assistant"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize troubleshooting agent"""
        self.console = Console()
        self.llm_client = llm_client or LLMClient()
        self.executor = CommandExecutor()
        self.display = DisplayManager()

    def start_diagnosis(self, initial_symptom: Optional[str] = None):
        """
        Start interactive troubleshooting session
        
        Args:
            initial_symptom: Initial problem description (optional)
        """
        self.console.print(Panel(
            "[bold blue]🔍 System Troubleshooting Agent[/bold blue]\n\n"
            "[dim]I'll help diagnose your system issue through a series of questions.[/dim]\n"
            "[dim]Type 'exit' to quit, 'skip' to skip a question.[/dim]",
            title="Troubleshooting Session",
            border_style="blue"
        ))

        symptoms = []
        if initial_symptom:
            symptoms.append(initial_symptom)
            self.console.print(f"\n[bold]Initial Symptom:[/bold] {initial_symptom}")

        # Gather information through questions
        questions_asked = 0
        max_questions = 10

        while questions_asked < max_questions:
            # Generate next question or diagnosis
            response = self._get_next_step(symptoms)
            
            if response.get("diagnosis_ready"):
                # Provide diagnosis
                self._provide_diagnosis(response, symptoms)
                break
            
            # Ask question
            question = response.get("question", "Can you describe the problem?")
            self.console.print(f"\n[bold cyan]❓ {question}[/bold cyan]")
            
            answer = Prompt.ask("[dim]Your answer[/dim]", default="")
            
            if answer.lower() in ["exit", "quit"]:
                self.console.print("[yellow]Troubleshooting session ended.[/yellow]")
                break
            
            if answer.lower() == "skip":
                continue
            
            symptoms.append(f"Q: {question}\nA: {answer}")
            questions_asked += 1

    def _get_next_step(self, symptoms: List[str]) -> Dict[str, Any]:
        """Get next question or diagnosis from AI"""
        context = "\n".join(symptoms) if symptoms else "No symptoms collected yet."
        
        prompt = f"""You are a Linux system troubleshooting expert. Based on the symptoms collected, either:
1. Ask ONE clarifying question to narrow down the issue
2. Provide a diagnosis if you have enough information

Symptoms collected so far:
{context}

If you have enough information to diagnose, provide:
- Probable root cause
- Confidence level
- Step-by-step fixes

If you need more info, ask ONE specific question.

Return as JSON:
{{
  "diagnosis_ready": true/false,
  "question": "question to ask (if not ready)",
  "root_cause": "diagnosis (if ready)",
  "confidence": "high|medium|low",
  "fixes": [
    {{
      "step": 1,
      "action": "what to do",
      "command": "command to run (optional)",
      "explanation": "why this helps"
    }}
  ]
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a Linux system troubleshooting expert. Diagnose issues systematically."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            return {
                "diagnosis_ready": False,
                "question": f"Error generating question: {str(e)}",
                "error": str(e)
            }

    def _provide_diagnosis(self, diagnosis: Dict[str, Any], symptoms: List[str]):
        """Provide diagnosis and fixes"""
        self.console.print("\n" + "="*70)
        self.console.print(Panel(
            "[bold green]✅ Diagnosis Complete[/bold green]",
            border_style="green"
        ))
        
        root_cause = diagnosis.get("root_cause", "Unknown issue")
        confidence = diagnosis.get("confidence", "medium")
        
        confidence_icon = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🔴"
        
        self.console.print(f"\n[bold]🔍 Probable Root Cause:[/bold]")
        self.console.print(f"{confidence_icon} {root_cause}")
        self.console.print(f"[dim]Confidence: {confidence}[/dim]")
        
        fixes = diagnosis.get("fixes", [])
        if fixes:
            self.console.print(f"\n[bold]🔧 Recommended Fixes:[/bold]")
            
            for fix in fixes:
                step = fix.get("step", "?")
                action = fix.get("action", "")
                command = fix.get("command", "")
                explanation = fix.get("explanation", "")
                
                fix_panel = Panel(
                    f"[bold]Step {step}:[/bold] {action}\n\n"
                    f"[dim]{explanation}[/dim]",
                    title=f"Fix {step}",
                    border_style="blue"
                )
                
                if command:
                    fix_panel.renderable += f"\n[green]Command:[/green] {command}"
                
                self.console.print(fix_panel)
                
                # Ask if user wants to execute
                if command:
                    if Confirm.ask(f"\n[bold]Execute fix {step}?[/bold]", default=False):
                        self._execute_fix(command, action)
        
        self.console.print("\n" + "="*70)

    def _execute_fix(self, command: str, description: str):
        """Execute a fix command"""
        self.console.print(f"\n[bold]🚀 Executing:[/bold] [green]{command}[/green]")
        
        result = self.executor.execute_commands([command], [description])
        
        if result["results"][0]["success"]:
            self.console.print("[green]✅ Fix executed successfully![/green]")
        else:
            self.console.print("[red]❌ Fix failed. Check the error output above.[/red]")

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response"""
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
            
            response = json.loads(content)
            
            # Validate
            if not isinstance(response, dict):
                raise ValueError("Response is not a dictionary")
            
            if "diagnosis_ready" not in response:
                response["diagnosis_ready"] = False
            
            return response
            
        except Exception as e:
            return {
                "diagnosis_ready": False,
                "question": "Can you describe what's not working?",
                "error": str(e)
            }
