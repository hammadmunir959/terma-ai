"""Conversational agent that answers questions naturally and executes commands when needed"""

from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager


class ConversationalAgent:
    """Agent that handles conversational queries and executes commands when needed"""

    def __init__(self, llm_client: Optional[LLMClient] = None, working_directory: Optional[str] = None):
        """Initialize the conversational agent"""
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()
        self.executor = CommandExecutor(working_directory=working_directory)
        self.display = DisplayManager()
        self.console = Console()

    def process_query(
        self, 
        user_query: str, 
        auto_execute: bool = True,
        confirm_risky: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query - answer conversationally or execute commands as needed
        
        Args:
            user_query: The user's question or request
            auto_execute: If True, automatically execute safe commands
            confirm_risky: If True, ask for confirmation before risky commands
            
        Returns:
            Dict with response and execution results
        """
        # Step 1: Analyze the query
        self.console.print(f"[dim]🤔 Analyzing query...[/dim]")
        analysis = self.llm_client.analyze_query(user_query, self.executor.get_working_directory())
        
        needs_execution = analysis.get("needs_execution", True)
        query_type = analysis.get("query_type", "command_request")
        
        # Step 2: Handle based on analysis
        if not needs_execution:
            # Pure conversational response
            self.console.print(f"[dim]💬 Generating conversational response...[/dim]\n")
            response = self.llm_client.generate_conversational_response(
                user_query,
                command_results=None,
                working_directory=self.executor.get_working_directory()
            )
            
            # Display response in a nice panel
            panel = Panel(
                Markdown(response),
                title="[bold cyan]💬 Response[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            self.console.print(panel)
            
            return {
                "type": "conversational",
                "response": response,
                "executed_commands": False,
                "query_type": query_type
            }
        
        else:
            # Query needs command execution
            self.console.print(f"[dim]🔧 Generating commands...[/dim]\n")
            
            # Generate commands
            working_dir = self.executor.get_working_directory()
            llm_response = self.llm_client.generate_commands(user_query, working_directory=working_dir)
            
            if llm_response.get("error"):
                error_msg = llm_response.get("error", "Unknown error")
                self.console.print(f"[red]❌ Error: {error_msg}[/red]")
                return {
                    "type": "error",
                    "error": error_msg,
                    "executed_commands": False
                }
            
            commands = llm_response.get("commands", [])
            explanations = llm_response.get("explanations", [])
            
            if not commands:
                response = self.llm_client.generate_conversational_response(
                    user_query,
                    command_results=None,
                    working_directory=working_dir
                )
                panel = Panel(
                    Markdown(response),
                    title="[bold yellow]💬 Response[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                )
                self.console.print(panel)
                return {
                    "type": "conversational",
                    "response": response,
                    "executed_commands": False
                }
            
            # Show commands
            self.display.show_commands(commands, explanations)
            
            # Safety check
            safety_result = self.safety_checker.check_commands(commands)
            
            # Handle risky commands
            if safety_result.get("has_risky"):
                self.display.show_risky_commands(safety_result["risky_commands"])
                has_critical = any(
                    c.get("risk_level") == "CRITICAL" 
                    for c in safety_result.get("risky_commands", [])
                )
                
                if confirm_risky:
                    self.console.print("[dim]⚠️  Risky commands detected - confirmation required[/dim]")
                    if not self.display.confirm_risky_execution(
                        len(safety_result["risky_commands"]),
                        len(commands),
                        has_critical
                    ):
                        self.console.print("[yellow]Execution cancelled[/yellow]")
                        return {
                            "type": "cancelled",
                            "executed_commands": False,
                            "commands": commands
                        }
            else:
                if auto_execute:
                    self.console.print("[dim]✓ Safe commands - executing automatically...[/dim]")
            
            # Execute commands
            self.display.show_execution_start()
            execution_result = self.executor.execute_commands(commands, explanations)
            
            # Show execution results
            self.display.show_execution_results(execution_result["results"], verbose=False)
            
            # Generate natural language summary
            self.console.print(f"\n[dim]💬 Generating response summary...[/dim]\n")
            response = self.llm_client.generate_conversational_response(
                user_query,
                command_results=execution_result["results"],
                working_directory=working_dir
            )
            
            # Display response in a nice panel
            panel = Panel(
                Markdown(response),
                title="[bold green]✅ Summary[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(panel)
            
            return {
                "type": "execution_with_summary",
                "response": response,
                "executed_commands": True,
                "commands": commands,
                "execution_result": execution_result,
                "query_type": query_type
            }

