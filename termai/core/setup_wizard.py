"""AI-guided environment setup wizard"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from .llm import LLMClient
from .planner import TaskPlanner
from .executor import CommandExecutor
from .display import DisplayManager
from .safety import SafetyChecker


class SetupWizard:
    """AI-guided setup wizard for development environments"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize setup wizard"""
        self.console = Console()
        self.llm_client = llm_client or LLMClient()
        self.planner = TaskPlanner(self.llm_client)
        self.executor = CommandExecutor()
        self.display = DisplayManager()
        self.safety_checker = SafetyChecker()

    def setup_environment(self, environment_type: str, options: Optional[Dict[str, Any]] = None):
        """
        Set up a development environment
        
        Args:
            environment_type: Type of environment (e.g., "django", "nodejs", "python")
            options: Additional options (version, project name, etc.)
        """
        self.console.print(Panel(
            f"[bold blue]🚀 Environment Setup Wizard[/bold blue]\n\n"
            f"[dim]Setting up: {environment_type}[/dim]",
            title="Setup Wizard",
            border_style="blue"
        ))

        # Generate setup plan
        setup_request = self._build_setup_request(environment_type, options or {})
        
        self.console.print(f"[dim]📋 Planning setup for: {environment_type}[/dim]")
        
        plan = self.planner.plan_task(setup_request)
        
        if plan.get("error"):
            self.display.show_error(plan["error"])
            return
        
        steps = plan.get("steps", [])
        if not steps:
            self.display.show_error("No setup steps generated")
            return
        
        # Show setup plan
        self.console.print(f"\n[bold]📋 Setup Plan:[/bold] {plan.get('summary', environment_type)}")
        self.console.print(f"[dim]Total steps: {len(steps)}[/dim]\n")
        
        for i, step in enumerate(steps, 1):
            self.console.print(f"[bold cyan]{i}. {step.get('description', '')}[/bold cyan]")
            self.console.print(f"   [dim]{step.get('command', '')}[/dim]")
        
        # Confirm setup
        if not Confirm.ask("\n[bold]Proceed with setup?[/bold]", default=True):
            self.console.print("[yellow]Setup cancelled[/yellow]")
            return
        
        # Execute setup
        self.console.print("\n[bold green]🚀 Starting setup...[/bold green]\n")
        
        results = []
        for i, step in enumerate(steps, 1):
            step_num = step.get("step", i)
            description = step.get("description", "")
            command = step.get("command", "")
            
            self.console.print(f"[bold]Step {step_num}/{len(steps)}:[/bold] {description}")
            self.console.print(f"[dim]Executing: {command}[/dim]\n")
            
            # Safety check
            safety_result = self.safety_checker.check_commands([command])
            
            if safety_result.get("has_risky"):
                self.display.show_risky_commands(safety_result["risky_commands"])
                has_critical = any(c.get("risk_level") == "CRITICAL" for c in safety_result.get("risky_commands", []))
                
                if not self.display.confirm_risky_execution(1, 1, has_critical):
                    self.console.print(f"[yellow]Step {step_num} skipped. Continuing...[/yellow]")
                    results.append({
                        "step": step_num,
                        "success": False,
                        "skipped": True
                    })
                    continue
            
            # Execute step
            execution_result = self.executor.execute_commands([command], [description])
            step_result = execution_result["results"][0] if execution_result["results"] else {}
            
            if step_result.get("success"):
                self.console.print(f"[green]✅ Step {step_num} completed[/green]\n")
            else:
                self.console.print(f"[red]❌ Step {step_num} failed[/red]")
                self.console.print(f"[dim]{step_result.get('stderr', 'Unknown error')}[/dim]\n")
                
                # Ask if user wants to continue
                if not Confirm.ask("[bold]Continue with remaining steps?[/bold]", default=True):
                    self.console.print("[yellow]Setup aborted[/yellow]")
                    break
            
            results.append({
                "step": step_num,
                "success": step_result.get("success", False),
                "command": command
            })
        
        # Summary
        successful = sum(1 for r in results if r.get("success"))
        total = len(results)
        
        self.console.print("\n" + "="*70)
        self.console.print(Panel(
            f"[bold]Setup Summary[/bold]\n\n"
            f"✅ Completed: {successful}/{total} steps\n"
            f"{'🎉 Setup completed successfully!' if successful == total else '⚠️  Some steps failed'}",
            border_style="green" if successful == total else "yellow"
        ))

    def _build_setup_request(self, environment_type: str, options: Dict[str, Any]) -> str:
        """Build setup request from environment type and options"""
        request_parts = [f"Set up a complete {environment_type} development environment"]
        
        if options.get("version"):
            request_parts.append(f"using version {options['version']}")
        
        if options.get("project_name"):
            request_parts.append(f"for project '{options['project_name']}'")
        
        if options.get("database"):
            request_parts.append(f"with {options['database']} database")
        
        if options.get("features"):
            request_parts.append(f"including: {', '.join(options['features'])}")
        
        return ". ".join(request_parts) + "."

    def list_templates(self) -> List[str]:
        """List available environment templates"""
        return [
            "django",
            "flask",
            "nodejs",
            "react",
            "vue",
            "python",
            "rust",
            "go",
            "java",
            "php",
            "ruby",
            "full-stack"
        ]
