"""API Key Setup and Configuration Helper"""

import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv, set_key, find_dotenv

console = Console()


class APIKeySetupError(Exception):
    """Custom exception for API key setup errors"""
    pass


def check_api_key() -> Optional[str]:
    """
    Check if API key is set. Returns the API key if found, None otherwise.
    
    Returns:
        API key string if found, None otherwise
    """
    load_dotenv()
    api_key = os.getenv("API_KEY") or os.getenv("OPENROUTER_API_KEY")
    return api_key


def show_api_key_instructions():
    """Display instructions for setting up OpenRouter API key"""
    instructions = """
🔑 OpenRouter API Key Setup Required

To use Terma AI, you need an OpenRouter API key. Here's how to get one:

📝 Step 1: Get Your API Key
   1. Visit: https://openrouter.ai/
   2. Sign up for a free account (if you don't have one)
   3. Go to: https://openrouter.ai/keys
   4. Click "Create Key" or copy your existing key
   5. Your key will look like: sk-or-v1-xxxxxxxxxxxxxxxxxxxxx

📝 Step 2: Set Your API Key

   Option A: Using .env file (Recommended)
   ────────────────────────────────────────
   Create a .env file in your current directory or home folder:
   
   echo "API_KEY=sk-or-v1-your-key-here" > .env
   
   Or use the interactive setup:
   terma setup-api

   Option B: Using Environment Variable
   ─────────────────────────────────────
   export API_KEY=sk-or-v1-your-key-here
   
   To make it permanent, add to ~/.bashrc or ~/.zshrc:
   echo 'export API_KEY=sk-or-v1-your-key-here' >> ~/.bashrc

📝 Step 3: Verify Setup
   terma config
   
   You should see: API Key: ✅ Set

💡 Free Tier Available
   OpenRouter offers free access to many models. No credit card required!

🔗 Links:
   • Get API Key: https://openrouter.ai/keys
   • Documentation: https://openrouter.ai/docs
   • Supported Models: https://openrouter.ai/models
"""
    
    console.print(Panel(
        instructions,
        title="[bold yellow]⚠️  API Key Not Configured[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    ))


def setup_api_key_interactive() -> bool:
    """
    Interactive setup for API key.
    
    Returns:
        True if setup was successful, False otherwise
    """
    console.print("\n[bold cyan]🔧 Terma AI API Key Setup[/bold cyan]\n")
    
    # Check if .env file exists
    env_path = find_dotenv()
    if not env_path:
        # Try to create in current directory
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            env_path.touch()
    else:
        env_path = Path(env_path)
    
    console.print(f"[dim]Configuration file: {env_path}[/dim]\n")
    
    # Get API key from user
    api_key = Prompt.ask(
        "Enter your OpenRouter API key",
        default="",
        show_default=False
    ).strip()
    
    if not api_key:
        console.print("[red]❌ No API key provided. Setup cancelled.[/red]")
        return False
    
    # Validate key format (basic check)
    if not api_key.startswith("sk-or-v1-") and not api_key.startswith("sk-"):
        console.print("[yellow]⚠️  Warning: API key format looks unusual. Make sure it's correct.[/yellow]")
        if not Confirm.ask("Continue anyway?"):
            return False
    
    # Save to .env file
    try:
        set_key(str(env_path), "API_KEY", api_key)
        console.print(f"\n[green]✅ API key saved to {env_path}[/green]")
        
        # Reload environment
        load_dotenv(env_path, override=True)
        
        console.print("\n[bold green]🎉 Setup complete![/bold green]")
        console.print("You can now use Terma AI commands.\n")
        console.print("[dim]Tip: Run 'terma config' to verify your configuration[/dim]\n")
        
        return True
    except Exception as e:
        console.print(f"[red]❌ Error saving API key: {str(e)}[/red]")
        return False


def require_api_key():
    """
    Check for API key and show instructions if missing.
    Raises APIKeySetupError with helpful message if not found.
    """
    api_key = check_api_key()
    
    if not api_key:
        show_api_key_instructions()
        raise APIKeySetupError(
            "API_KEY not configured. Please set up your OpenRouter API key first.\n"
            "Run 'terma setup-api' for interactive setup, or see instructions above."
        )
    
    return api_key

