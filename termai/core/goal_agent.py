"""Goal-Oriented Agent for Terma AI"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager


class GoalAgent:
    """Goal-oriented agent that understands, plans, and executes user goals"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize the goal agent"""
        self.console = Console()
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()
        self.display = DisplayManager()
        self.executor = CommandExecutor()

    def process_goal(self, user_goal: str, auto_confirm: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process a user goal from start to finish
        
        Args:
            user_goal: Natural language goal description
            auto_confirm: Automatically confirm steps without asking
            dry_run: Preview plan without executing
            
        Returns:
            Complete goal execution results
        """
        self.console.print(Panel(
            f"[bold blue]🎯 Goal-Oriented Agent[/bold blue]\n\n"
            f"[dim]Goal: {user_goal}[/dim]",
            title="Goal Processing",
            border_style="blue"
        ))

        # Step 1: Understand and clarify goal
        goal_understanding = self._understand_goal(user_goal)
        
        if goal_understanding.get("needs_clarification"):
            clarified_goal = self._clarification_loop(goal_understanding)
            if not clarified_goal:
                return {"cancelled": True, "reason": "User cancelled clarification"}
            user_goal = clarified_goal

        # Step 2: Decompose goal into steps
        plan = self._decompose_goal(user_goal)
        
        if plan.get("error"):
            self.display.show_error(plan["error"])
            return plan

        steps = plan.get("steps", [])
        if not steps:
            self.display.show_error("No steps generated for goal")
            return {"error": "No steps generated"}

        # Step 3: Show plan and confirm
        self._show_goal_plan(plan, steps)
        
        if dry_run:
            self.console.print("\n[bold yellow]🔍 DRY RUN - Goal will not be executed[/bold yellow]")
            return {
                "goal": user_goal,
                "plan": plan,
                "steps": steps,
                "dry_run": True
            }

        if not auto_confirm:
            if not Confirm.ask("\n[bold]Proceed with goal execution?[/bold]", default=True):
                return {"cancelled": True, "reason": "User cancelled"}

        # Step 4: Execute steps sequentially
        execution_results = self._execute_goal_steps(steps, auto_confirm)

        # Step 5: Generate completion summary
        summary = self._generate_completion_summary(user_goal, steps, execution_results)

        return {
            "goal": user_goal,
            "plan": plan,
            "steps": steps,
            "execution_results": execution_results,
            "summary": summary,
            "success": execution_results.get("all_successful", False)
        }

    def _understand_goal(self, goal: str) -> Dict[str, Any]:
        """Understand the goal and identify ambiguities"""
        prompt = f"""Analyze this user goal and identify if clarification is needed:

Goal: "{goal}"

Determine:
1. Is the goal clear and actionable?
2. What ambiguities exist?
3. What questions should be asked?

Return as JSON:
{{
  "needs_clarification": true/false,
  "ambiguities": ["ambiguity1", "ambiguity2"],
  "questions": ["question1", "question2"],
  "interpreted_goal": "clarified version of goal"
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a goal analysis expert. Identify ambiguities in user goals."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            content = response.choices[0].message.content
            return self._parse_json_response(content)
            
        except Exception as e:
            return {
                "needs_clarification": False,
                "interpreted_goal": goal,
                "error": str(e)
            }

    def _clarification_loop(self, understanding: Dict[str, Any]) -> Optional[str]:
        """Interactive clarification loop"""
        questions = understanding.get("questions", [])
        ambiguities = understanding.get("ambiguities", [])
        
        if not questions:
            return understanding.get("interpreted_goal", "")
        
        # Filter out obvious questions (we know we're on Linux)
        filtered_questions = []
        for q in questions:
            q_lower = q.lower()
            # Skip OS questions - we know it's Linux
            if any(word in q_lower for word in ["operating system", "os", "windows", "macos", "environment"]):
                continue
            # Skip obvious context questions
            if any(word in q_lower for word in ["shell environment", "terminal", "command line"]):
                continue
            filtered_questions.append(q)
        
        if not filtered_questions:
            # No critical questions, use interpreted goal
            return understanding.get("interpreted_goal", "")
        
        self.console.print("\n[bold yellow]❓ Goal Clarification Needed[/bold yellow]")
        
        if ambiguities:
            self.console.print("\n[dim]Ambiguities detected:[/dim]")
            for amb in ambiguities[:3]:  # Show max 3
                self.console.print(f"  • {amb}")
        
        self.console.print("\n[dim]You can type 'skip' to use defaults, or 'cancel' to abort[/dim]")
        
        answers = []
        for i, question in enumerate(filtered_questions, 1):
            self.console.print(f"\n[bold cyan]Question {i}/{len(filtered_questions)}:[/bold cyan] {question}")
            answer = Prompt.ask("[dim]Your answer (or 'skip' for default)[/dim]", default="skip")
            
            if answer.lower() in ["cancel", "exit", "abort"]:
                return None
            
            if answer.lower() == "skip":
                continue
            
            answers.append(f"Q: {question}\nA: {answer}")
        
        # Reconstruct clarified goal
        clarified = understanding.get("interpreted_goal", "")
        if answers:
            clarified += " " + " ".join([a.split("A: ")[1] for a in answers if "A: " in a])
        
        return clarified if clarified else understanding.get("interpreted_goal", "")

    def _decompose_goal(self, goal: str) -> Dict[str, Any]:
        """Decompose goal into sequential steps with dependencies"""
        prompt = f"""Break down this goal into ordered, executable steps:

Goal: "{goal}"

Requirements:
- Each step must be a single bash command
- Steps must be in correct dependency order
- Include safety considerations
- Identify which steps are risky

Return as JSON:
{{
  "summary": "Brief goal summary",
  "steps": [
    {{
      "step": 1,
      "description": "What this step does",
      "command": "bash command",
      "dependencies": [],
      "risky": false,
      "requires_confirmation": false
    }}
  ],
  "estimated_time": "estimated completion time",
  "warnings": ["warning1", "warning2"]
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a goal decomposition expert. Break goals into safe, ordered steps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            plan = self._parse_json_response(content)
            
            # Validate and enhance steps
            steps = plan.get("steps", [])
            for step in steps:
                if "dependencies" not in step:
                    step["dependencies"] = []
                if "risky" not in step:
                    step["risky"] = False
                if "requires_confirmation" not in step:
                    step["requires_confirmation"] = False
            
            return plan
            
        except Exception as e:
            return {
                "error": f"Failed to decompose goal: {str(e)}",
                "steps": []
            }

    def _show_goal_plan(self, plan: Dict[str, Any], steps: List[Dict[str, Any]]):
        """Display the goal plan"""
        summary = plan.get("summary", "Goal execution plan")
        estimated_time = plan.get("estimated_time", "Unknown")
        warnings = plan.get("warnings", [])
        
        self.console.print(f"\n[bold]📋 Goal Plan:[/bold] {summary}")
        self.console.print(f"[dim]Estimated time: {estimated_time}[/dim]")
        
        if warnings:
            self.console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
            for warning in warnings:
                self.console.print(f"  • {warning}")
        
        # Show steps table
        table = Table(title="Execution Steps", show_header=True, header_style="bold magenta")
        table.add_column("Step", style="cyan", width=6)
        table.add_column("Description", style="white")
        table.add_column("Command", style="green", no_wrap=False)
        table.add_column("Risk", style="yellow", width=8)
        
        for step in steps:
            step_num = step.get("step", "?")
            desc = step.get("description", "")
            cmd = step.get("command", "")
            risk_icon = "⚠️" if step.get("risky") else "✅"
            
            table.add_row(str(step_num), desc, cmd[:50] + "..." if len(cmd) > 50 else cmd, risk_icon)
        
        self.console.print(table)

    def _execute_goal_steps(self, steps: List[Dict[str, Any]], auto_confirm: bool = False) -> Dict[str, Any]:
        """Execute goal steps sequentially with monitoring"""
        self.console.print("\n[bold green]🚀 Executing Goal Steps...[/bold green]\n")
        
        results = []
        start_time = time.time()
        
        for i, step in enumerate(steps, 1):
            step_num = step.get("step", i)
            description = step.get("description", "")
            command = step.get("command", "")
            is_risky = step.get("risky", False)
            requires_confirmation = step.get("requires_confirmation", False)
            
            # Show step
            step_panel = Panel(
                f"[bold]Step {step_num}:[/bold] {description}\n\n"
                f"[dim]Command:[/dim] [green]{command}[/green]",
                title=f"Step {step_num}/{len(steps)}",
                border_style="blue"
            )
            self.console.print(step_panel)
            
            # Safety check
            safety_result = self.safety_checker.check_commands([command])
            
            if safety_result.get("has_risky"):
                self.display.show_risky_commands(safety_result["risky_commands"])
                has_critical = any(c.get("risk_level") == "CRITICAL" for c in safety_result.get("risky_commands", []))
                
                if not auto_confirm:
                    if not self.display.confirm_risky_execution(1, 1, has_critical):
                        self.console.print(f"[yellow]Step {step_num} skipped. Continue?[/yellow]")
                        if not Confirm.ask("", default=True):
                            return {
                                "aborted": True,
                                "completed_steps": i - 1,
                                "total_steps": len(steps),
                                "results": results
                            }
                        results.append({
                            "step": step_num,
                            "skipped": True,
                            "reason": "User cancelled risky operation"
                        })
                        continue
            
            # Confirmation for steps that require it
            if requires_confirmation and not auto_confirm:
                if not Confirm.ask(f"[bold]Execute step {step_num}?[/bold]", default=True):
                    results.append({
                        "step": step_num,
                        "skipped": True,
                        "reason": "User cancelled"
                    })
                    continue
            
            # Execute step
            step_start = time.time()
            execution_result = self.executor.execute_commands([command], [description])
            step_end = time.time()
            
            step_result = execution_result["results"][0] if execution_result["results"] else {}
            step_result["step"] = step_num
            step_result["description"] = description
            step_result["command"] = command
            step_result["execution_time"] = step_end - step_start
            
            results.append(step_result)
            
            # Check if step failed
            if not step_result.get("success", False):
                self.console.print(f"[red]❌ Step {step_num} failed[/red]")
                self.console.print(f"[dim]Error: {step_result.get('stderr', 'Unknown error')}[/dim]")
                
                # Ask what to do
                if not auto_confirm:
                    self.console.print("\n[bold]What would you like to do?[/bold]")
                    choice = Prompt.ask(
                        "[dim]Options: retry, skip, abort[/dim]",
                        default="skip"
                    )
                    
                    if choice.lower() == "retry":
                        # Retry the step
                        retry_result = self.executor.execute_commands([command], [description])
                        if retry_result["results"][0].get("success"):
                            results[-1] = retry_result["results"][0]
                            results[-1]["step"] = step_num
                            results[-1]["retried"] = True
                            self.console.print("[green]✅ Retry successful![/green]")
                        else:
                            self.console.print("[red]❌ Retry also failed[/red]")
                    elif choice.lower() == "abort":
                        return {
                            "aborted": True,
                            "completed_steps": i - 1,
                            "total_steps": len(steps),
                            "results": results
                        }
                    # else: skip (continue)
        
        end_time = time.time()
        
        return {
            "completed": True,
            "total_steps": len(steps),
            "results": results,
            "all_successful": all(r.get("success", False) for r in results if not r.get("skipped")),
            "total_time": end_time - start_time
        }

    def _generate_completion_summary(self, goal: str, steps: List[Dict[str, Any]], 
                                     execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate completion summary with learning insights"""
        results = execution_results.get("results", [])
        successful = sum(1 for r in results if r.get("success") and not r.get("skipped"))
        failed = sum(1 for r in results if not r.get("success") and not r.get("skipped"))
        skipped = sum(1 for r in results if r.get("skipped"))
        total_time = execution_results.get("total_time", 0)
        
        # Generate AI summary
        summary_prompt = f"""Summarize this goal execution:

Goal: {goal}
Total Steps: {len(steps)}
Successful: {successful}
Failed: {failed}
Skipped: {skipped}
Total Time: {total_time:.2f}s

Provide:
1. Brief execution summary
2. Key achievements
3. Any issues encountered
4. Suggestions for improvement or safer alternatives
5. Learning insights"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a goal execution analyst. Provide clear summaries and learning insights."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.4,
                max_tokens=400
            )
            
            ai_summary = response.choices[0].message.content
            
            return {
                "goal": goal,
                "total_steps": len(steps),
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "total_time": total_time,
                "all_successful": execution_results.get("all_successful", False),
                "ai_summary": ai_summary,
                "steps_detail": [
                    {
                        "step": r.get("step"),
                        "success": r.get("success"),
                        "skipped": r.get("skipped"),
                        "description": r.get("description", "")
                    }
                    for r in results
                ]
            }
            
        except Exception as e:
            return {
                "goal": goal,
                "total_steps": len(steps),
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "total_time": total_time,
                "error": f"Could not generate AI summary: {str(e)}"
            }

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
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
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "needs_clarification": False}
        except Exception as e:
            return {"error": str(e), "needs_clarification": False}

    def show_summary(self, summary: Dict[str, Any]):
        """Display goal completion summary"""
        self.console.print("\n" + "="*70)
        
        status_icon = "✅" if summary.get("all_successful") else "⚠️"
        status_color = "green" if summary.get("all_successful") else "yellow"
        
        summary_panel = Panel(
            f"[bold]{status_icon} Goal Execution Summary[/bold]\n\n"
            f"Goal: {summary.get('goal', 'Unknown')}\n"
            f"Steps: {summary.get('successful', 0)}/{summary.get('total_steps', 0)} successful\n"
            f"Time: {summary.get('total_time', 0):.2f}s",
            title="Summary",
            border_style=status_color
        )
        self.console.print(summary_panel)
        
        if summary.get("ai_summary"):
            self.console.print("\n[bold]📊 AI Analysis:[/bold]")
            self.console.print(summary["ai_summary"])
        
        # Show step details
        if summary.get("steps_detail"):
            table = Table(title="Step Details", show_header=True)
            table.add_column("Step", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Description", style="white")
            
            for step_detail in summary["steps_detail"]:
                step_num = step_detail.get("step", "?")
                if step_detail.get("skipped"):
                    status = "[yellow]⏭️  Skipped[/yellow]"
                elif step_detail.get("success"):
                    status = "[green]✅ Success[/green]"
                else:
                    status = "[red]❌ Failed[/red]"
                
                desc = step_detail.get("description", "")
                table.add_row(str(step_num), status, desc)
            
            self.console.print(table)
        
        self.console.print("="*70)
