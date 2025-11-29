"""Command executor for running bash commands safely"""

import os
import subprocess
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from .file_helper import correct_filename_in_command


class CommandExecutor:
    """Execute bash commands safely with proper output handling"""

    def __init__(self, working_directory: Optional[str] = None):
        """Initialize the command executor"""
        self.working_directory = working_directory or os.getcwd()
        self.last_execution_time = 0.0
        self.console = Console()

    def execute_commands(self, commands: List[str], explanations: List[str]) -> Dict[str, Any]:
        """
        Execute a list of commands sequentially

        Args:
            commands: List of bash commands to execute
            explanations: Explanations for each command

        Returns:
            Dict with execution results
        """
        results = []

        for i, (cmd, explanation) in enumerate(zip(commands, explanations)):
            # Auto-correct filenames (case-insensitive matching)
            corrected_cmd, was_corrected = correct_filename_in_command(cmd, self.working_directory)
            if was_corrected:
                self.console.print(f"\n[dim yellow]🔧 Auto-corrected filename:[/dim yellow] [dim]{cmd}[/dim] → [green]{corrected_cmd}[/green]")
                cmd = corrected_cmd
            
            self.console.print(f"\n[bold]🔄 Executing:[/bold] [cyan]{cmd}[/cyan]")
            self.console.print(f"[dim]📝 {explanation}[/dim]")

            start_time = time.time()
            result = self._execute_single_command(cmd)
            end_time = time.time()

            result["execution_time"] = end_time - start_time
            result["command_index"] = i
            result["command"] = cmd
            result["explanation"] = explanation

            results.append(result)

            # Stop execution if a command fails critically
            if result["return_code"] != 0 and self._is_critical_failure(cmd, result):
                self.console.print(f"[red]❌ Critical failure in command {i+1}, stopping execution[/red]")
                break

        return {
            "total_commands": len(commands),
            "executed_commands": len(results),
            "results": results,
            "all_successful": all(r["return_code"] == 0 for r in results)
        }

    def _execute_single_command(self, command: str) -> Dict[str, Any]:
        """Execute a single bash command"""
        try:
            # Execute command in bash shell
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters
                timeout=30  # 30 second timeout
            )

            return {
                "return_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "success": process.returncode == 0,
                "timed_out": False
            }

        except subprocess.TimeoutExpired:
            return {
                "return_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 30 seconds",
                "success": False,
                "timed_out": True
            }

        except Exception as e:
            return {
                "return_code": -1,
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "success": False,
                "timed_out": False
            }

    def _is_critical_failure(self, command: str, result: Dict[str, Any]) -> bool:
        """Determine if a command failure should stop execution"""
        # For now, we'll continue execution even if commands fail
        # This can be made more sophisticated later
        return False

    def set_working_directory(self, directory: str):
        """Set the working directory for command execution"""
        if Path(directory).exists() and Path(directory).is_dir():
            self.working_directory = directory
        else:
            raise ValueError(f"Directory does not exist: {directory}")

    def get_working_directory(self) -> str:
        """Get the current working directory"""
        return self.working_directory

    def test_command(self, command: str) -> bool:
        """Test if a command would execute successfully (dry run)"""
        # This is a basic implementation - could be enhanced
        try:
            # Just check if the command exists (first word)
            cmd_parts = command.strip().split()
            if not cmd_parts:
                return False

            base_cmd = cmd_parts[0]
            result = subprocess.run(
                f"which {base_cmd}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
