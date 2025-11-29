"""Multi-step task planner for complex operations"""

import json
from typing import List, Dict, Any, Optional
from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager


class TaskPlanner:
    """Plan and execute multi-step tasks"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize the task planner"""
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()
        self.display = DisplayManager()

    def plan_task(self, user_request: str) -> Dict[str, Any]:
        """
        Break down a user request into ordered steps
        
        Args:
            user_request: Natural language description of the task
            
        Returns:
            Dict with plan details
        """
        planning_prompt = self._get_planning_prompt(user_request)
        
        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": self._get_planning_system_prompt()},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            plan = self._parse_plan(content)
            return plan
            
        except Exception as e:
            return {
                "error": f"Failed to create plan: {str(e)}",
                "steps": [],
                "summary": ""
            }

    def execute_plan(self, plan: Dict[str, Any], executor: CommandExecutor, 
                     dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute a planned task step by step
        
        Args:
            plan: Plan dictionary with steps
            executor: Command executor instance
            dry_run: If True, only show what would be executed
            
        Returns:
            Execution results
        """
        if plan.get("error"):
            return {"error": plan["error"], "results": []}
        
        steps = plan.get("steps", [])
        if not steps:
            return {"error": "No steps in plan", "results": []}
        
        results = []
        
        self.display.console.print(f"\n[bold]📋 Task Plan: {plan.get('summary', 'Multi-step task')}[/bold]")
        self.display.console.print(f"[dim]Total steps: {len(steps)}[/dim]\n")
        
        for i, step in enumerate(steps, 1):
            step_num = step.get("step", i)
            description = step.get("description", "")
            command = step.get("command", "")
            
            # Show step
            from rich.panel import Panel
            step_panel = Panel(
                f"[bold]Step {step_num}:[/bold] {description}\n\n"
                f"[dim]Command:[/dim] [green]{command}[/green]",
                title=f"Step {step_num}/{len(steps)}",
                border_style="blue"
            )
            self.display.console.print(step_panel)
            
            if dry_run:
                self.display.console.print("[yellow]🔍 DRY RUN - Command not executed[/yellow]\n")
                results.append({
                    "step": step_num,
                    "command": command,
                    "description": description,
                    "executed": False,
                    "dry_run": True
                })
                continue
            
            # Safety check
            safety_result = self.safety_checker.check_commands([command])
            
            if safety_result.get("has_risky"):
                self.display.show_risky_commands(safety_result["risky_commands"])
                has_critical = any(c.get("risk_level") == "CRITICAL" for c in safety_result.get("risky_commands", []))
                
                if not self.display.confirm_risky_execution(1, 1, has_critical):
                    self.display.console.print(f"[yellow]Step {step_num} cancelled. Aborting plan execution.[/yellow]")
                    return {
                        "aborted": True,
                        "completed_steps": i - 1,
                        "total_steps": len(steps),
                        "results": results
                    }
            
            # Execute step
            self.display.console.print(f"[dim]Executing step {step_num}...[/dim]")
            execution_result = executor.execute_commands([command], [description])
            
            step_result = execution_result["results"][0] if execution_result["results"] else {}
            step_result["step"] = step_num
            step_result["description"] = description
            step_result["command"] = command
            step_result["executed"] = True
            
            results.append(step_result)
            
            # Check if step failed critically
            if not step_result.get("success", False):
                self.display.console.print(f"[red]Step {step_num} failed. Continue? (y/n):[/red]")
                # For now, continue on failure - could be made configurable
                continue
        
        return {
            "completed": True,
            "total_steps": len(steps),
            "results": results
        }

    def _get_planning_system_prompt(self) -> str:
        """Get system prompt for task planning"""
        return """You are a Linux task planner for Terma AI.

Break down user requests into ordered, executable steps.

Return your response as valid JSON with this structure:
{
  "summary": "Brief description of the task",
  "steps": [
    {
      "step": 1,
      "description": "What this step does",
      "command": "bash command to execute"
    },
    ...
  ]
}

Guidelines:
- Break complex tasks into 2-10 steps
- Each step should be a single bash command
- Steps must be in correct execution order
- Include dependencies (e.g., create directory before copying files)
- Use safe commands when possible
- Explain what each step does clearly"""

    def _get_planning_prompt(self, user_request: str) -> str:
        """Get user prompt for planning"""
        return f"""Break down this task into ordered steps: "{user_request}"

Return only valid JSON with the plan."""

    def _parse_plan(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into plan structure"""
        try:
            # Try to extract JSON from response
            content = content.strip()
            
            # Find JSON block if wrapped in markdown
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            plan = json.loads(content)
            
            # Validate structure
            if not isinstance(plan, dict):
                raise ValueError("Plan is not a dictionary")
            
            if "steps" not in plan:
                raise ValueError("Plan missing 'steps' field")
            
            # Ensure steps have required fields
            for step in plan["steps"]:
                if "command" not in step:
                    step["command"] = ""
                if "description" not in step:
                    step["description"] = f"Step {step.get('step', '?')}"
            
            return plan
            
        except json.JSONDecodeError as e:
            return {
                "error": f"Invalid JSON in plan response: {str(e)}",
                "steps": [],
                "summary": ""
            }
        except Exception as e:
            return {
                "error": f"Failed to parse plan: {str(e)}",
                "steps": [],
                "summary": ""
            }
