"""Display utilities for rich terminal output"""

from typing import List, Dict, Any
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from .file_helper import suggest_files_for_error
from rich.prompt import Confirm


console = Console()


class DisplayManager:
    """Manages rich terminal output for Terma AI"""

    def __init__(self):
        self.console = console

    def show_welcome(self):
        """Show welcome message"""
        welcome_text = Text("🤖 Terma AI - Natural Language Terminal Agent", style="bold blue")
        self.console.print(Panel(welcome_text, title="Welcome", border_style="blue"))

    def show_processing(self, query: str):
        """Show query processing message"""
        self.console.print(f"🔍 [bold cyan]Processing:[/bold cyan] {query}")

    def show_commands(self, commands: List[str], explanations: List[str]):
        """Display generated commands in a nice format"""
        table = Table(title="📋 Generated Commands", show_header=True, header_style="bold magenta")
        table.add_column("Command", style="green", no_wrap=True)
        table.add_column("Explanation", style="yellow")

        for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
            table.add_row(f"{i}. {cmd}", explanation)

        self.console.print(table)

    def show_safety_warnings(self, warnings: List[Dict[str, Any]]):
        """Display safety warnings"""
        if not warnings:
            return

        warning_text = Text("⚠️  Safety Warnings:", style="bold yellow")
        self.console.print(warning_text)

        for warning in warnings:
            self.console.print(f"  • [yellow]{warning['command']}[/yellow]: {warning['warning']}")

    def show_risky_commands(self, risky_commands: List[Dict[str, Any]]):
        """Display risky commands that require extra confirmation"""
        if not risky_commands:
            return

        # Group by risk level
        critical = [c for c in risky_commands if c.get("risk_level") == "CRITICAL"]
        high = [c for c in risky_commands if c.get("risk_level") == "HIGH"]
        medium = [c for c in risky_commands if c.get("risk_level") == "MEDIUM"]

        if critical:
            self.console.print("\n[bold red]⚠️  CRITICAL RISK COMMANDS DETECTED ⚠️[/bold red]")
            self.console.print("[red]These commands can DESTROY your system or cause irreversible damage![/red]\n")
            
            for risky in critical:
                panel = Panel(
                    f"[bold red]{risky['command']}[/bold red]\n\n[white]{risky['reason']}[/white]",
                    title=f"🚨 CRITICAL - Command {risky['index'] + 1}",
                    border_style="red"
                )
                self.console.print(panel)

        if high:
            self.console.print("\n[bold yellow]⚠️  HIGH RISK COMMANDS DETECTED ⚠️[/bold yellow]")
            self.console.print("[yellow]These commands modify system files or require elevated privileges![/yellow]\n")
            
            for risky in high:
                panel = Panel(
                    f"[yellow]{risky['command']}[/yellow]\n\n[white]{risky['reason']}[/white]",
                    title=f"⚠️  HIGH RISK - Command {risky['index'] + 1}",
                    border_style="yellow"
                )
                self.console.print(panel)

        if medium:
            self.console.print("\n[bold yellow]⚠️  RISKY COMMANDS DETECTED ⚠️[/bold yellow]\n")
            
            for risky in medium:
                panel = Panel(
                    f"[yellow]{risky['command']}[/yellow]\n\n[white]{risky['reason']}[/white]",
                    title=f"⚠️  RISKY - Command {risky['index'] + 1}",
                    border_style="yellow"
                )
                self.console.print(panel)

    def show_alternatives(self, blocked_commands: List[Dict[str, Any]], safety_checker):
        """Show safer alternatives for blocked commands"""
        if not blocked_commands:
            return

        self.console.print("\n💡 [bold green]Safer Alternatives:[/bold green]")

        for blocked in blocked_commands:
            alternatives = safety_checker.suggest_alternatives(blocked["command"])
            if alternatives:
                alt_text = "\n".join(f"  • {alt}" for alt in alternatives)
                self.console.print(alt_text)

    def confirm_execution(self, command_count: int) -> bool:
        """Get user confirmation for command execution"""
        return Confirm.ask(
            f"🔒 Ready to execute {command_count} safe command(s)?",
            default=False
        )

    def confirm_risky_execution(self, risky_count: int, total_count: int, has_critical: bool = False) -> bool:
        """Get user confirmation for risky command execution with extra warnings"""
        self.console.print("\n" + "="*70)
        
        if has_critical:
            warning_panel = Panel(
                "[bold red]⚠️  CRITICAL RISK WARNING ⚠️[/bold red]\n\n"
                "[red]You are about to execute commands that can DESTROY your system![/red]\n"
                "[red]These operations may be IRREVERSIBLE![/red]\n\n"
                f"[white]Total risky commands: {risky_count}[/white]\n"
                f"[white]Total commands: {total_count}[/white]",
                title="🚨 DANGER",
                border_style="red"
            )
        else:
            warning_panel = Panel(
                "[bold yellow]⚠️  RISKY OPERATION WARNING ⚠️[/bold yellow]\n\n"
                "[yellow]You are about to execute commands that may modify system files or require elevated privileges.[/yellow]\n\n"
                f"[white]Total risky commands: {risky_count}[/white]\n"
                f"[white]Total commands: {total_count}[/white]",
                title="⚠️  WARNING",
                border_style="yellow"
            )
        
        self.console.print(warning_panel)
        self.console.print("="*70 + "\n")
        
        if has_critical:
            # Require explicit "yes" for critical commands
            response = Confirm.ask(
                "[bold red]Are you ABSOLUTELY SURE you want to proceed? Type 'yes' to confirm:[/bold red]",
                default=False
            )
            if response:
                # Double confirmation for critical
                return Confirm.ask(
                    "[bold red]FINAL WARNING: This may destroy your system. Type 'yes' again to proceed:[/bold red]",
                    default=False
                )
            return False
        else:
            return Confirm.ask(
                f"[bold yellow]Do you want to proceed with {risky_count} risky command(s)?[/bold yellow]",
                default=False
            )

    def show_execution_start(self):
        """Show execution start message"""
        self.console.print("\n🚀 [bold green]Executing commands...[/bold green]")

    def show_command_execution(self, command: str, explanation: str):
        """Show individual command execution"""
        self.console.print(f"\n🔄 [bold blue]Executing:[/bold blue] {command}")
        self.console.print(f"📝 [dim]{explanation}[/dim]")

    def show_execution_results(self, results: List[Dict[str, Any]], verbose: bool = False):
        """Display execution results"""
        successful = sum(1 for r in results if r.get("success", False) or r.get("return_code", 1) == 0)
        total = len(results)

        # Calculate success rate
        if total > 0:
            success_rate = (successful / total) * 100
            success_rate_str = f"{success_rate:.1f}%"
        else:
            success_rate_str = "0%"

        # Show command output for each result
        for i, result in enumerate(results, 1):
            command = result.get("command", "Unknown command")
            stdout = result.get("stdout", "").strip()
            stderr = result.get("stderr", "").strip()
            return_code = result.get("return_code", -1)
            success = result.get("success", return_code == 0)
            
            # Show output
            if stdout:
                self.console.print(f"\n[bold green]📄 Output:[/bold green]")
                self.console.print(stdout)
            
            if stderr:
                self.console.print(f"\n[bold red]⚠️  Error Output:[/bold red]")
                self.console.print(stderr)
                
                # Check for "file not found" errors and suggest similar files
                if "No such file or directory" in stderr or "cannot open" in stderr.lower():
                    cwd = os.getcwd()
                    suggestions = suggest_files_for_error(stderr, cwd)
                    if suggestions:
                        self.console.print(f"\n[bold yellow]💡 Did you mean one of these files?[/bold yellow]")
                        for suggestion in suggestions[:5]:  # Show max 5 suggestions
                            self.console.print(f"  • [cyan]{suggestion}[/cyan]")
            
            # Show status if command failed
            if not success:
                self.console.print(f"\n[bold red]❌ Command failed with return code: {return_code}[/bold red]")
            elif not stdout and not stderr:
                # Command succeeded but produced no output
                self.console.print(f"\n[dim]✓ Command completed successfully (no output)[/dim]")

        # Summary
        self.console.print("\n")
        summary_table = Table(title="📊 Execution Summary", show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Commands executed", str(total))
        summary_table.add_row("Success rate", success_rate_str)

        self.console.print(summary_table)

        # Detailed results if verbose
        if verbose and results:
            self.console.print("\n[bold]Detailed Results:[/bold]")
            for result in results:
                status_icon = "✅" if result.get("success", False) else "❌"
                status_color = "green" if result.get("success", False) else "red"
                execution_time = result.get("execution_time", 0.0)

                panel_content = f"[bold]{status_icon} {result.get('command', 'Unknown')}[/bold]\n"
                panel_content += f"Execution time: {execution_time:.2f}s\n"
                panel_content += f"[dim]Return code: {result.get('return_code', -1)}[/dim]"

                panel = Panel(
                    panel_content,
                    title=f"Command {result.get('command_index', 0) + 1}",
                    border_style=status_color
                )

                self.console.print(panel)

    def show_error(self, message: str, verbose: bool = False, traceback: str = None):
        """Display error message"""
        error_text = Text(f"❌ {message}", style="bold red")
        self.console.print(error_text)

        if verbose and traceback:
            self.console.print("\n[dim]Traceback:[/dim]")
            self.console.print(traceback)

    def show_success(self, message: str):
        """Display success message"""
        success_text = Text(f"✅ {message}", style="bold green")
        self.console.print(success_text)
