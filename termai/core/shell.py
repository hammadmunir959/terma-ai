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
from .conversational import ConversationalAgent
from .react_agent import ReActAgent


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
        
        # Initialize conversational agent
        self.conversational_agent = ConversationalAgent(
            llm_client=self.llm_client,
            working_directory=self.executor.get_working_directory()
        )
        
        # Initialize ReAct agent
        self.react_agent = ReActAgent(
            llm_client=self.llm_client,
            working_directory=self.executor.get_working_directory()
        )
        
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
            "[dim]Use 'react <goal>' for ReAct agentic mode[/dim]\n"
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
        
        elif cmd.startswith("react "):
            # Handle ReAct agent command
            goal = command[6:].strip()  # Remove "react " prefix
            if goal:
                self._process_react_goal(goal)
            else:
                self.console.print("[yellow]Usage: react <goal>[/yellow]")
                self.console.print("[dim]Example: react create a Python project with README[/dim]")
            return True
        
        return False

    def _process_command(self, user_input: str):
        """Process a user command through AI using conversational agent"""
        # Add to context
        self.context_history.append(f"User: {user_input}")
        self.command_history.append(user_input)
        
        # Update agent working directory
        self.conversational_agent.executor = self.executor
        
        # Use conversational agent to process the query
        # This will automatically determine if commands are needed and provide natural language responses
        result = self.conversational_agent.process_query(
            user_input,
            auto_execute=True,
            confirm_risky=True
        )
        
        # Add to context based on result type
        if result.get("executed_commands"):
            self.context_history.append(f"AI: {result.get('response', 'Command executed')}")
        else:
            self.context_history.append(f"AI: {result.get('response', 'Responded')}")
    
    def _process_react_goal(self, goal: str):
        """Process a goal using ReAct agent with enhanced features"""
        # Add to context
        self.context_history.append(f"User: react {goal}")
        self.command_history.append(f"react {goal}")
        
        # Update ReAct agent working directory
        self.react_agent.executor = self.executor
        
        # Use ReAct agent to achieve the goal with enhanced features
        # Default to 7 iterations, but encourage 3-5
        result = self.react_agent.achieve_goal(
            goal,
            auto_confirm=False,  # Ask for confirmation in shell
            max_iterations=7,    # Default to 7, encourage 3-5
            verbose=True         # Show all step-by-step feedback
        )
        
        # Show summary with natural language response
        self.react_agent.show_summary(result)
        
        # Add to context with natural language summary
        natural_summary = result.get("natural_language_summary", "")
        if natural_summary:
            # Use first sentence or first 100 chars of summary
            summary_preview = natural_summary.split('.')[0] if '.' in natural_summary else natural_summary[:100]
            self.context_history.append(f"AI: {summary_preview}")
        else:
            status = result.get("status", "unknown")
            if result.get("goal_achieved"):
                self.context_history.append(f"AI: Goal achieved! ({status})")
            else:
                self.context_history.append(f"AI: Goal processing completed ({status})")

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
  [cyan]react <goal>[/cyan]            - Use ReAct agent to achieve a goal

[bold]Usage:[/bold]
  [bold]Regular mode:[/bold] Just type your request in natural language:
  [dim]TermaShell > list files[/dim]
  [dim]TermaShell > create a new directory[/dim]
  [dim]TermaShell > show disk usage[/dim]
  
  [bold]ReAct mode:[/bold] Use ReAct agent for complex goals:
  [dim]TermaShell > react create a Python project with README[/dim]
  [dim]TermaShell > react organize all .txt files into documents folder[/dim]
  [dim]TermaShell > react find and display the largest file[/dim]
  
  [bold]ReAct Agent Features:[/bold]
  - Creates and manages a todo list
  - Updates observations at each step
  - Provides step-by-step feedback ("Now I'm doing X", "Next I'll do Y")
  - Works systematically through todos
  - Generates natural language summaries
  - Uses Observe → Reason → Plan → Act loop (3-7 iterations recommended)
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
