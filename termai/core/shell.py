"""Interactive Terma Shell for persistent AI conversations"""

import sys
from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager
from .preferences import Preferences
from .api_setup import APIKeySetupError


class TermaShell:
    """Interactive shell for continuous AI terminal interaction"""

    def __init__(self, cwd: Optional[str] = None):
        """Initialize the Terma Shell"""
        self.console = Console()
        self.preferences = Preferences()
        try:
            self.llm_client = LLMClient(preferences=self.preferences)
        except APIKeySetupError:
            # Re-raise to be handled by CLI
            raise
        self.safety_checker = SafetyChecker()
        self.executor = CommandExecutor(cwd)
        self.display = DisplayManager()
        
        # Session context
        self.context_history: List[str] = []
        self.command_history: List[str] = []
        self.running = True

    def start(self):
        """Start the interactive shell"""
        self._show_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]TermaShell[/bold cyan]", default="")
                
                if not user_input.strip():
                    continue
                
                # Handle shell commands
                if self._handle_shell_command(user_input):
                    continue
                
                # Process AI command
                self._process_command(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit the shell[/yellow]")
            except EOFError:
                self._exit_shell()
                break
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

    def _show_welcome(self):
        """Show welcome message"""
        welcome = Panel(
            "[bold blue]🤖 Terma Shell - Interactive AI Terminal[/bold blue]\n\n"
            "[dim]Type your commands in natural language[/dim]\n"
            "[dim]Use 'exit' to quit, 'clear' to clear context, 'help' for help[/dim]",
            title="Welcome",
            border_style="blue"
        )
        self.console.print(welcome)

    def _handle_shell_command(self, command: str) -> bool:
        """Handle built-in shell commands. Returns True if handled."""
        cmd = command.strip().lower()
        
        if cmd == "exit" or cmd == "quit":
            self._exit_shell()
            return True
        
        elif cmd == "clear":
            self.context_history.clear()
            self.console.print("[green]Context cleared[/green]")
            return True
        
        elif cmd == "help":
            self._show_help()
            return True
        
        elif cmd == "history":
            self._show_history()
            return True
        
        elif cmd.startswith("cd "):
            # Handle directory change
            path = command[3:].strip()
            try:
                self.executor.set_working_directory(path)
                self.console.print(f"[green]Changed directory to: {path}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
            return True
        
        return False

    def _process_command(self, user_input: str):
        """Process a user command through AI"""
        # Add to context
        self.context_history.append(f"User: {user_input}")
        self.command_history.append(user_input)
        
        # Build context-aware prompt
        context_prompt = self._build_context_prompt(user_input)
        
        # Generate commands
        self.console.print(f"[dim]🤔 Processing: {user_input}[/dim]")
        llm_response = self.llm_client.generate_commands(context_prompt)
        
        if llm_response.get("error"):
            self.console.print(f"[red]❌ Error: {llm_response['error']}[/red]")
            return
        
        commands = llm_response.get("commands", [])
        explanations = llm_response.get("explanations", [])
        
        if not commands:
            self.console.print("[yellow]⚠️  No commands generated[/yellow]")
            return
        
        # Safety check
        safety_result = self.safety_checker.check_commands(commands)
        
        # Show commands
        self.display.show_commands(commands, explanations)
        
        # Handle risky commands
        if safety_result.get("has_risky"):
            self.display.show_risky_commands(safety_result["risky_commands"])
            
            # Confirmation for risky
            has_critical = any(c.get("risk_level") == "CRITICAL" for c in safety_result.get("risky_commands", []))
            if not self.display.confirm_risky_execution(
                len(safety_result["risky_commands"]),
                len(commands),
                has_critical
            ):
                self.console.print("[yellow]Execution cancelled[/yellow]")
                return
        
        # Regular confirmation
        if not self.display.confirm_execution(len(commands)):
            self.console.print("[yellow]Execution cancelled[/yellow]")
            return
        
        # Execute
        all_commands = safety_result["safe_commands"].copy()
        for risky in safety_result.get("risky_commands", []):
            all_commands.insert(risky["index"], risky["command"])
        
        self.display.show_execution_start()
        execution_result = self.executor.execute_commands(
            all_commands,
            explanations[:len(all_commands)]
        )
        
        # Show results
        self.display.show_execution_results(execution_result["results"], verbose=False)
        
        # Add to context
        self.context_history.append(f"AI: Executed {len(commands)} command(s)")

    def _build_context_prompt(self, current_input: str) -> str:
        """Build context-aware prompt from history"""
        if not self.context_history:
            return current_input
        
        # Include recent context (last 5 interactions)
        recent_context = "\n".join(self.context_history[-5:])
        return f"Context from previous commands:\n{recent_context}\n\nCurrent request: {current_input}"

    def _show_help(self):
        """Show help message"""
        help_text = """
[bold]Terma Shell Commands:[/bold]

  [cyan]exit[/cyan], [cyan]quit[/cyan]  - Exit the shell
  [cyan]clear[/cyan]                   - Clear conversation context
  [cyan]history[/cyan]                 - Show command history
  [cyan]help[/cyan]                    - Show this help message
  [cyan]cd <path>[/cyan]               - Change working directory

[bold]Usage:[/bold]
  Just type your request in natural language:
  [dim]TermaShell > list files[/dim]
  [dim]TermaShell > create a new directory[/dim]
  [dim]TermaShell > show disk usage[/dim]
        """
        self.console.print(Panel(help_text, title="Help", border_style="cyan"))

    def _show_history(self):
        """Show command history"""
        if not self.command_history:
            self.console.print("[dim]No commands in history[/dim]")
            return
        
        history_text = "\n".join(f"{i+1}. {cmd}" for i, cmd in enumerate(self.command_history[-10:]))
        self.console.print(Panel(history_text, title="Command History (last 10)", border_style="blue"))

    def _exit_shell(self):
        """Exit the shell gracefully"""
        self.running = False
        self.console.print("\n[green]👋 Thanks for using Terma Shell![/green]")
