"""Command-line interface for Terma AI"""

import typer
import os
from pathlib import Path
from typing import Optional
import sys

from . import __version__
from .core.llm import LLMClient
from .core.safety import SafetyChecker
from .core.executor import CommandExecutor
from .core.display import DisplayManager
from .core.shell import TermaShell
from .core.planner import TaskPlanner
from .core.preferences import Preferences
from .core.teaching import TeachingMode
from .core.autofix import AutoFix
from .core.troubleshoot import TroubleshootingAgent
from .core.setup_wizard import SetupWizard
from .core.git_assistant import GitAssistant
from .core.network_diagnostic import NetworkDiagnostic
from .core.goal_agent import GoalAgent
from .core.api_setup import APIKeySetupError, setup_api_key_interactive, check_api_key
from .core.conversational import ConversationalAgent
from .core.react_agent import ReActAgent

app = typer.Typer(
    name="termai",
    help="Terma AI - Natural Language Terminal Agent",
    add_completion=False,
    no_args_is_help=True
)


@app.callback(invoke_without_command=True)
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
        is_eager=True
    )
):
    """Terma AI converts natural language to safe bash commands"""
    if version:
        typer.echo(f"Terma AI version {__version__}")
        raise typer.Exit()


def handle_api_key_error(func):
    """Decorator to handle API key setup errors consistently"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIKeySetupError:
            # Error message already shown by require_api_key()
            raise typer.Exit(1)
    return wrapper


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Natural language description of what you want to do"),
    confirm: bool = typer.Option(True, "--confirm/--no-confirm", help="Require confirmation before executing commands"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for command execution"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show commands without executing them")
):
    """
    Convert natural language to bash commands and execute them safely.

    Examples:
        termai run "find all large files in current directory"
        termai run show disk usage --no-confirm
        termai run list files sorted by size --cwd /home/user
        termai run check git status
    """
    # Combine query with any remaining arguments
    if query:
        query_parts = [query]
    else:
        query_parts = []
    
    # Get remaining arguments from context
    if ctx.args:
        query_parts.extend(ctx.args)
    
    # Join all parts into a single query
    if not query_parts:
        typer.echo("❌ Error: Query is required")
        typer.echo("Usage: termai run <query>")
        typer.echo("Example: termai run check git status")
        raise typer.Exit(1)
    
    query = " ".join(query_parts)
    
    display = DisplayManager()

    try:
        # Initialize components (will check for API key)
        llm_client = LLMClient()
        safety_checker = SafetyChecker()
        executor = CommandExecutor(cwd)

        if verbose:
            display.show_welcome()
            display.console.print(f"📍 Working directory: {executor.get_working_directory()}")

        # Generate commands from natural language
        display.show_processing(query)
        working_dir = executor.get_working_directory()
        llm_response = llm_client.generate_commands(query, working_directory=working_dir)

        if llm_response.get("error"):
            display.show_error(llm_response["error"])
            raise typer.Exit(1)

        commands = llm_response.get("commands", [])
        explanations = llm_response.get("explanations", [])

        if not commands:
            display.show_error("No commands generated. Please try a different query.")
            raise typer.Exit(1)

        # Display generated commands
        display.show_commands(commands, explanations)

        # Safety check
        safety_result = safety_checker.check_commands(commands)

        # Show risky commands prominently
        if safety_result.get("has_risky"):
            display.show_risky_commands(safety_result["risky_commands"])

        # Show warnings if any
        display.show_safety_warnings(safety_result["warnings"])

        # Prepare all commands for execution (safe + risky)
        all_commands = safety_result["safe_commands"].copy()
        risky_commands_list = safety_result.get("risky_commands", [])
        
        # Add risky commands to execution list (maintaining order)
        for risky in risky_commands_list:
            all_commands.insert(risky["index"], risky["command"])

        # Confirmation - only for risky commands, safe commands auto-execute
        if confirm:
            # Check if there are risky commands
            if safety_result.get("has_risky"):
                has_critical = any(c.get("risk_level") == "CRITICAL" for c in risky_commands_list)
                display.console.print("[dim]⚠️  Risky commands detected - confirmation required[/dim]")
                if not display.confirm_risky_execution(
                    len(risky_commands_list),
                    len(all_commands),
                    has_critical
                ):
                    display.console.print("[yellow]Execution cancelled by user[/yellow]")
                    raise typer.Exit(0)
            else:
                # Safe commands execute automatically
                display.console.print("[dim]✓ Safe commands - executing automatically...[/dim]")

        # Dry-run mode
        if dry_run:
            display.console.print("\n[bold yellow]🔍 DRY RUN MODE - Commands will NOT be executed[/bold yellow]\n")
            for i, cmd in enumerate(all_commands, 1):
                display.console.print(f"[dim]{i}. {cmd}[/dim]")
            display.console.print("\n[yellow]Use without --dry-run to execute these commands[/yellow]")
            raise typer.Exit(0)

        # Execute commands (both safe and risky after confirmation)
        display.show_execution_start()
        execution_result = executor.execute_commands(
            all_commands,
            explanations[:len(all_commands)]
        )

        # Display results
        display.show_execution_results(execution_result["results"], verbose)

    except APIKeySetupError as e:
        # API key setup error - already shows instructions
        raise typer.Exit(1)
    except typer.Exit as e:
        # Re-raise Exit exceptions (normal flow)
        raise e
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except Exception as e:
        import traceback
        display.show_error(f"Unexpected error: {str(e)}", verbose, traceback.format_exc() if verbose else None)
        raise typer.Exit(1)


@app.command()
def test(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed test output")
):
    """Test Terma AI components and API connectivity"""
    typer.echo("🧪 Testing Terma AI components...")

    tests_passed = 0
    total_tests = 0

    # Test LLM client
    total_tests += 1
    try:
        llm_client = LLMClient()
        if llm_client.test_connection():
            typer.echo("✅ LLM API connection successful")
            tests_passed += 1
        else:
            typer.echo("❌ LLM API connection failed")
    except APIKeySetupError:
        typer.echo("❌ LLM API connection failed: API key not configured")
        typer.echo("💡 Run 'terma setup-api' to configure your API key")
    except Exception as e:
        typer.echo(f"❌ LLM client error: {str(e)}")

    # Test safety checker
    total_tests += 1
    try:
        safety_checker = SafetyChecker()
        test_commands = ["ls -la", "rm -rf /"]
        result = safety_checker.check_commands(test_commands)

        if not result["safe"] and len(result.get("risky_commands", [])) == 1:
            typer.echo("✅ Safety checker working correctly")
            tests_passed += 1
        else:
            typer.echo("❌ Safety checker test failed")
    except Exception as e:
        typer.echo(f"❌ Safety checker error: {str(e)}")

    # Test command executor
    total_tests += 1
    try:
        executor = CommandExecutor()
        if executor.test_command("echo hello"):
            typer.echo("✅ Command executor basic test passed")
            tests_passed += 1
        else:
            typer.echo("❌ Command executor test failed")
    except Exception as e:
        typer.echo(f"❌ Command executor error: {str(e)}")

    typer.echo(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        typer.echo("🎉 All tests passed!")
        raise typer.Exit(0)
    else:
        typer.echo("⚠️  Some tests failed")
        raise typer.Exit(1)


@app.command()
def config():
    """Show current configuration"""
    try:
        llm_client = LLMClient(require_key=False)
        config = llm_client.config

        typer.echo("⚙️  Current Configuration:")
        typer.echo(f"  Provider: {config.get('provider', 'unknown')}")
        typer.echo(f"  Model: {config.get('model', 'unknown')}")
        typer.echo(f"  Temperature: {config.get('temperature', 'unknown')}")
        typer.echo(f"  Max Tokens: {config.get('max_tokens', 'unknown')}")
        typer.echo(f"  API Base: {config.get('api_base', 'unknown')}")

        # Check API key
        api_key = check_api_key()
        if api_key:
            # Show masked key
            masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
            typer.echo(f"  API Key: ✅ Set ({masked_key})")
        else:
            typer.echo(f"  API Key: ❌ Missing")
            typer.echo("\n💡 Run 'terma setup-api' to configure your API key")

    except Exception as e:
        typer.echo(f"❌ Error loading configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("setup-api")
def setup_api():
    """
    Interactive setup for OpenRouter API key.
    
    This command will guide you through setting up your API key.
    """
    try:
        if setup_api_key_interactive():
            raise typer.Exit(0)
        else:
            raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 Setup cancelled")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"❌ Error during setup: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def chat(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Your question or request"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for command execution"),
    auto_execute: bool = typer.Option(True, "--auto-execute/--no-auto-execute", help="Automatically execute safe commands"),
    confirm_risky: bool = typer.Option(True, "--confirm-risky/--no-confirm-risky", help="Ask for confirmation before risky commands")
):
    """
    Chat with Terma AI - Ask questions or request actions in natural language.
    
    Terma AI will:
    - Answer questions conversationally (like ChatGPT)
    - Execute commands when needed and provide natural language summaries
    
    Examples:
        terma chat "what is git?"
        terma chat "list files in current directory"
        terma chat "explain how ls command works"
        terma chat "show me the contents of README.md"
        terma chat check git status
    """
    try:
        # Combine query with any remaining arguments
        if query:
            query_parts = [query]
        else:
            query_parts = []
        
        # Get remaining arguments from context
        if ctx.args:
            query_parts.extend(ctx.args)
        
        # Join all parts into a single query
        if not query_parts:
            typer.echo("❌ Error: Query is required")
            typer.echo("Usage: terma chat <your question or request>")
            typer.echo("Examples:")
            typer.echo("  terma chat \"what is git?\"")
            typer.echo("  terma chat \"list files in current directory\"")
            typer.echo("  terma chat check git status")
            raise typer.Exit(1)
        
        user_query = " ".join(query_parts)
        
        # Initialize components (will check for API key)
        llm_client = LLMClient()
        working_dir = cwd or os.getcwd()
        
        # Create conversational agent
        agent = ConversationalAgent(llm_client=llm_client, working_directory=working_dir)
        
        # Process the query
        result = agent.process_query(
            user_query,
            auto_execute=auto_execute,
            confirm_risky=confirm_risky
        )
        
        # Exit successfully
        raise typer.Exit(0)
        
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 Chat cancelled")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def shell(
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for the shell")
):
    """Start interactive Terma Shell for continuous AI conversations"""
    try:
        terma_shell = TermaShell(cwd)
        terma_shell.start()
    except KeyboardInterrupt:
        typer.echo("\n👋 Shell exited")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"❌ Error starting shell: {str(e)}", err=True)
        raise typer.Exit(1)


# Preferences commands
pref_app = typer.Typer(name="pref", help="Manage Terma AI preferences")
app.add_typer(pref_app)


@pref_app.command("list")
def pref_list():
    """List all current preferences"""
    try:
        prefs = Preferences()
        all_prefs = prefs.list_all()
        
        typer.echo("⚙️  Current Preferences:")
        for key, value in all_prefs.items():
            typer.echo(f"  {key}: {value}")
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@pref_app.command("set")
def pref_set(
    key: str = typer.Argument(..., help="Preference key to set"),
    value: str = typer.Argument(..., help="Value to set")
):
    """Set a preference value"""
    try:
        prefs = Preferences()
        
        # Convert value to appropriate type
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        
        prefs.set(key, value)
        typer.echo(f"✅ Set {key} = {value}")
    except ValueError as e:
        typer.echo(f"❌ Invalid preference: {str(e)}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@pref_app.command("get")
def pref_get(
    key: str = typer.Argument(..., help="Preference key to get")
):
    """Get a preference value"""
    try:
        prefs = Preferences()
        value = prefs.get(key)
        if value is not None:
            typer.echo(f"{key}: {value}")
        else:
            typer.echo(f"❌ Preference '{key}' not found", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@pref_app.command("reset")
def pref_reset():
    """Reset all preferences to defaults"""
    try:
        prefs = Preferences()
        prefs.reset()
        typer.echo("✅ Preferences reset to defaults")
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def plan(
    task: str = typer.Argument(..., help="Natural language description of the multi-step task"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for execution")
):
    """
    Plan and execute a multi-step task.
    
    Examples:
        termai plan "set up a Node.js project with Express"
        termai plan "create backup and compress files" --dry-run
    """
    display = DisplayManager()
    
    try:
        planner = TaskPlanner()
        executor = CommandExecutor(cwd)
        
        display.console.print(f"[bold cyan]📋 Planning task:[/bold cyan] {task}")
        
        # Create plan
        plan_result = planner.plan_task(task)
        
        if plan_result.get("error"):
            display.show_error(plan_result["error"])
            raise typer.Exit(1)
        
        # Show plan
        steps = plan_result.get("steps", [])
        if not steps:
            display.show_error("No steps generated in plan")
            raise typer.Exit(1)
        
        # Confirm execution
        if not dry_run:
            if not display.confirm_execution(len(steps)):
                display.console.print("[yellow]Plan execution cancelled[/yellow]")
                raise typer.Exit(0)
        
        # Execute plan
        execution_result = planner.execute_plan(plan_result, executor, dry_run=dry_run)
        
        if execution_result.get("aborted"):
            display.console.print(f"\n[yellow]Plan aborted after {execution_result['completed_steps']} steps[/yellow]")
        elif execution_result.get("completed"):
            display.console.print(f"\n[green]✅ Plan completed successfully![/green]")
            display.console.print(f"[dim]Executed {execution_result['total_steps']} steps[/dim]")
        
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except Exception as e:
        import traceback
        display.show_error(f"Unexpected error: {str(e)}", verbose=False, traceback=traceback.format_exc() if False else None)
        raise typer.Exit(1)


@app.command()
def explain(
    command: str = typer.Argument(..., help="Bash command to explain"),
    why: Optional[str] = typer.Option(None, "--why", help="Explain why this command was chosen for a request"),
    safer: bool = typer.Option(False, "--safer", help="Show safer alternatives"),
    breakdown: bool = typer.Option(False, "--breakdown", help="Break down the command step by step")
):
    """
    Explain what a command does and provide educational information.
    
    Examples:
        termai explain "rm -rf /tmp/test"
        termai explain "sudo apt update" --why "update system packages"
        termai explain "chmod 777 file" --safer
        termai explain "find . -name '*.py' -exec grep -l 'import' {} \\;" --breakdown
    """
    display = DisplayManager()
    teaching = TeachingMode()
    
    try:
        if breakdown:
            # Break down command
            steps = teaching.break_down_steps(command)
            display.console.print(f"\n[bold]📚 Breaking down:[/bold] [green]{command}[/green]\n")
            for step in steps:
                display.console.print(f"[bold cyan]{step['step']}[/bold cyan]")
                display.console.print(f"  {step['explanation']}\n")
        
        elif safer:
            # Show safer alternatives
            suggestions = teaching.suggest_safer_way(command)
            display.console.print(f"\n[bold]🛡️  Safer alternatives for:[/bold] [yellow]{command}[/yellow]\n")
            display.console.print(f"[bold]Risk Score:[/bold] {suggestions['risk_score']}/5\n")
            
            if suggestions.get("ai_suggestions"):
                display.console.print("[bold]AI Suggestions:[/bold]")
                display.console.print(suggestions["ai_suggestions"])
            
            if suggestions.get("pattern_based_alternatives"):
                display.console.print("\n[bold]Quick Alternatives:[/bold]")
                for alt in suggestions["pattern_based_alternatives"]:
                    display.console.print(f"  • {alt}")
        
        elif why:
            # Explain why command was chosen
            explanation = teaching.explain_why(command, why)
            display.console.print(f"\n[bold]💡 Why this command for '{why}':[/bold]\n")
            display.console.print(f"[green]{command}[/green]\n")
            display.console.print(explanation)
        
        else:
            # Full explanation
            explanation = teaching.explain_command(command)
            
            display.console.print(f"\n[bold]📖 Explanation:[/bold] [green]{explanation['command']}[/green]\n")
            display.console.print(explanation['explanation'])
            
            if explanation.get("risk_score", 0) > 1:
                display.console.print(f"\n[bold]⚠️  Risk Analysis:[/bold]")
                display.console.print(f"  Risk Score: {explanation['risk_score']}/5 ({explanation['risk_level']})")
                
                if explanation.get("potential_effects"):
                    display.console.print(f"\n  [bold]Potential Effects:[/bold]")
                    for effect in explanation["potential_effects"]:
                        display.console.print(f"    • {effect}")
                
                if explanation.get("safer_alternatives"):
                    display.console.print(f"\n  [bold]Safer Alternatives:[/bold]")
                    for alt in explanation["safer_alternatives"]:
                        display.console.print(f"    • {alt}")
    
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except Exception as e:
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


@app.command()
def fix(
    command: str = typer.Argument(..., help="The command that failed"),
    stderr: str = typer.Option("", "--stderr", help="Error output from the failed command"),
    stdout: str = typer.Option("", "--stdout", help="Standard output from the failed command"),
    return_code: int = typer.Option(1, "--return-code", help="Return code from failed command"),
    auto: bool = typer.Option(False, "--auto", help="Automatically execute the suggested fix"),
    teaching: bool = typer.Option(False, "--teaching", help="Show detailed explanations")
):
    """
    Analyze and fix terminal command errors.
    
    Examples:
        termai fix "npm install" --stderr "npm: command not found"
        termai fix "python script.py" --stderr "ModuleNotFoundError" --auto
        termai fix "docker run image" --stderr "permission denied" --teaching
    """
    autofix = AutoFix()
    
    try:
        result = autofix.fix_error(
            command=command,
            stderr=stderr,
            stdout=stdout,
            return_code=return_code,
            auto_execute=auto,
            teaching_mode=teaching
        )
        
        if result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
            raise typer.Exit(1)
    
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


@app.command()
def troubleshoot(
    symptom: Optional[str] = typer.Argument(None, help="Initial symptom or problem description")
):
    """
    Start interactive system troubleshooting session.
    
    The agent will ask questions to diagnose your system issue and provide guided fixes.
    
    Examples:
        termai troubleshoot
        termai troubleshoot "system is slow"
        termai troubleshoot "network connection issues"
    """
    try:
        agent = TroubleshootingAgent()
        agent.start_diagnosis(initial_symptom=symptom)
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 Troubleshooting session ended")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def setup(
    environment: str = typer.Argument(..., help="Type of environment to set up (e.g., django, nodejs, python)"),
    version: Optional[str] = typer.Option(None, "--version", help="Version to install"),
    project_name: Optional[str] = typer.Option(None, "--name", help="Project name"),
    database: Optional[str] = typer.Option(None, "--database", help="Database type (postgresql, mysql, sqlite)"),
    features: Optional[str] = typer.Option(None, "--features", help="Comma-separated list of features")
):
    """
    AI-guided environment setup wizard.
    
    Sets up complete development environments with dependencies, virtual environments, and configuration.
    
    Examples:
        termai setup django
        termai setup nodejs --version 18
        termai setup python --name myproject
        termai setup django --database postgresql --features "redis,cache"
    """
    try:
        wizard = SetupWizard()
        
        options = {}
        if version:
            options["version"] = version
        if project_name:
            options["project_name"] = project_name
        if database:
            options["database"] = database
        if features:
            options["features"] = [f.strip() for f in features.split(",")]
        
        wizard.setup_environment(environment, options)
    
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 Setup cancelled")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("setup-list")
def setup_list():
    """List available environment templates"""
    try:
        wizard = SetupWizard()
        templates = wizard.list_templates()
        
        typer.echo("📋 Available Environment Templates:")
        for template in templates:
            typer.echo(f"  • {template}")
        typer.echo("\nUse: termai setup <template>")
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


# Git Assistant commands
git_app = typer.Typer(name="git", help="Natural language Git commands")
app.add_typer(git_app)


@git_app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(
    ctx: typer.Context,
    request: Optional[str] = typer.Argument(None, help="Natural language Git request"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute the generated commands"),
    explain: bool = typer.Option(False, "--explain", help="Show detailed explanations")
):
    """
    Convert natural language to Git commands.
    
    Examples:
        termai git run "undo last commit but keep changes"
        termai git run create a new branch called feature --execute
        termai git run show recent commits --explain
        termai git run initialize terminal_ai/
        termai git run stage all files and commit with message
    """
    # Combine request with any remaining arguments
    if request:
        request_parts = [request]
    else:
        request_parts = []
    
    # Get remaining arguments from context
    if ctx.args:
        request_parts.extend(ctx.args)
    
    # Join all parts into a single request
    if not request_parts:
        typer.echo("❌ Error: Git request is required")
        typer.echo("Usage: termai git run <request>")
        typer.echo("Example: termai git run initialize repository")
        raise typer.Exit(1)
    
    request = " ".join(request_parts)
    
    try:
        assistant = GitAssistant()
        result = assistant.process_git_request(request, execute=execute, explain=explain)
        
        if result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
            raise typer.Exit(1)
        
        if result.get("warning"):
            display = DisplayManager()
            display.console.print(f"[yellow]⚠️  Warning:[/yellow] {result['warning']}")
    
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


# Network Diagnostic commands
network_app = typer.Typer(name="network", help="Network diagnostic tools")
app.add_typer(network_app)


@network_app.command("ping")
def network_ping(
    host: str = typer.Argument(..., help="Hostname or IP address to ping"),
    count: int = typer.Option(4, "--count", "-c", help="Number of ping packets"),
    explain: bool = typer.Option(True, "--explain/--no-explain", help="Show AI explanation")
):
    """Ping a host and get AI-explained results"""
    try:
        diagnostic = NetworkDiagnostic()
        result = diagnostic.ping(host, count=count, explain=explain)
        
        if not result.get("success") and result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
    
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


@network_app.command("trace")
def network_trace(
    host: str = typer.Argument(..., help="Hostname or IP address to trace"),
    explain: bool = typer.Option(True, "--explain/--no-explain", help="Show AI explanation")
):
    """Trace route to a host and get AI-explained results"""
    try:
        diagnostic = NetworkDiagnostic()
        result = diagnostic.trace_route(host, explain=explain)
        
        if not result.get("success") and result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
    
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


@network_app.command("port")
def network_port(
    host: str = typer.Argument(..., help="Hostname or IP address"),
    port: int = typer.Argument(..., help="Port number to check"),
    explain: bool = typer.Option(True, "--explain/--no-explain", help="Show AI explanation")
):
    """Check if a port is open and get AI-explained results"""
    try:
        diagnostic = NetworkDiagnostic()
        result = diagnostic.check_port(host, port, explain=explain)
        
        if not result.get("success") and result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
    
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


@network_app.command("dns")
def network_dns(
    hostname: str = typer.Argument(..., help="Hostname to lookup"),
    explain: bool = typer.Option(True, "--explain/--no-explain", help="Show AI explanation")
):
    """Perform DNS lookup and get AI-explained results"""
    try:
        diagnostic = NetworkDiagnostic()
        result = diagnostic.dns_lookup(hostname, explain=explain)
        
        if not result.get("success") and result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
    
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Error: {str(e)}")
        raise typer.Exit(1)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def react(
    ctx: typer.Context,
    goal: Optional[str] = typer.Argument(None, help="Goal to achieve using ReAct methodology"),
    auto_confirm: bool = typer.Option(False, "--auto", help="Auto-confirm risky actions without asking"),
    max_iterations: int = typer.Option(7, "--max-iterations", help="Maximum number of observe-reason-plan-act cycles (default: 7, 3-5 recommended)"),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Show detailed reasoning and observations"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for execution")
):
    """
    ReAct Agent: Fully agentic goal achievement using Observe-Reason-Plan-Act loop.
    
    The ReAct agent will:
    1. OBSERVE: Check current system state (files, directories, recent outputs)
    2. REASON: Analyze if goal is achieved, what's needed, what went wrong
    3. PLAN: Decide on next action(s) to take
    4. ACT: Execute the planned commands
    5. OBSERVE: Check results and loop back to reasoning
    
    This continues until:
    - Goal is achieved ✅
    - Goal is determined impossible ❌
    - Maximum iterations reached ⚠️
    
    Examples:
        terma react "create a Python project with README and requirements.txt"
        terma react "organize all .txt files into a documents folder"
        terma react "find and display the largest file in current directory"
        terma react --auto "set up a basic web server"
        terma react --max-iterations 10 "backup all important files"
    """
    # Combine goal with any remaining arguments
    if goal:
        goal_parts = [goal]
    else:
        goal_parts = []
    
    # Get remaining arguments from context
    if ctx.args:
        goal_parts.extend(ctx.args)
    
    # Join all parts into a single goal
    if not goal_parts:
        typer.echo("❌ Error: Goal is required")
        typer.echo("Usage: terma react <goal description>")
        typer.echo("Examples:")
        typer.echo("  terma react \"create a Python project with README\"")
        typer.echo("  terma react organize all text files")
        raise typer.Exit(1)
    
    goal_description = " ".join(goal_parts)
    
    try:
        # Initialize ReAct agent
        llm_client = LLMClient()
        working_dir = cwd or os.getcwd()
        agent = ReActAgent(llm_client=llm_client, working_directory=working_dir)
        
        # Achieve the goal
        result = agent.achieve_goal(
            goal_description,
            auto_confirm=auto_confirm,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        # Show summary
        agent.show_summary(result)
        
        # Exit with appropriate code
        if result.get("goal_achieved"):
            raise typer.Exit(0)
        elif result.get("status") == "impossible":
            raise typer.Exit(1)
        elif result.get("status") == "max_iterations":
            typer.echo("\n[yellow]⚠️  Maximum iterations reached. Goal may not be fully achieved.[/yellow]")
            raise typer.Exit(1)
        else:
            raise typer.Exit(0)
    
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 ReAct agent interrupted")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def goal(
    ctx: typer.Context,
    goal_description: Optional[str] = typer.Argument(None, help="Natural language goal description"),
    auto_confirm: bool = typer.Option(False, "--auto", help="Auto-confirm all steps without asking"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing")
):
    """
    Goal-Oriented Agent: Understand, plan, and execute complex goals.
    
    The agent will:
    1. Understand your goal and ask clarifying questions if needed
    2. Break it down into ordered steps
    3. Execute steps safely with monitoring
    4. Provide completion summary with learning insights
    
    Examples:
        termai goal "backup all my project files, compress them, and upload to Google Drive"
        termai goal setup a Node.js project with Express and TypeScript
        termai goal --auto check git status
        termai goal clean old log files and free up disk space --dry-run
        termai goal deploy my application to production --auto
    """
    # Combine goal_description with any remaining arguments
    if goal_description:
        goal_parts = [goal_description]
    else:
        goal_parts = []
    
    # Get remaining arguments from context
    if ctx.args:
        goal_parts.extend(ctx.args)
    
    # Join all parts into a single goal description
    if not goal_parts:
        typer.echo("❌ Error: Goal description is required")
        typer.echo("Usage: termai goal <goal description>")
        typer.echo("Example: termai goal check git status")
        raise typer.Exit(1)
    
    goal_description = " ".join(goal_parts)
    
    try:
        agent = GoalAgent()
        result = agent.process_goal(goal_description, auto_confirm=auto_confirm, dry_run=dry_run)
        
        if result.get("cancelled"):
            typer.echo("Goal execution cancelled")
            raise typer.Exit(0)
        
        if result.get("error"):
            display = DisplayManager()
            display.show_error(result["error"])
            raise typer.Exit(1)
        
        if result.get("summary"):
            agent.show_summary(result["summary"])
        
        if result.get("dry_run"):
            raise typer.Exit(0)
        
        if result.get("success"):
            raise typer.Exit(0)
        elif result.get("cancelled"):
            raise typer.Exit(0)
        else:
            raise typer.Exit(1)
    
    except APIKeySetupError:
        # Error message already shown by require_api_key()
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 Goal execution interrupted")
        raise typer.Exit(0)
    except Exception as e:
        display = DisplayManager()
        display.show_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def cli():
    """CLI entry point for pip-installed package"""
    app()


if __name__ == "__main__":
    app()
