"""Tests for command executor"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from termai.core.executor import CommandExecutor


class TestCommandExecutor:
    """Test the command executor functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.executor = CommandExecutor()

    def test_initialization(self):
        """Test executor initialization"""
        executor = CommandExecutor()
        assert executor.working_directory == os.getcwd()

        executor_custom = CommandExecutor("/tmp")
        assert executor_custom.working_directory == "/tmp"

    def test_set_working_directory(self):
        """Test setting working directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.executor.set_working_directory(tmpdir)
            assert self.executor.working_directory == tmpdir

    def test_set_invalid_working_directory(self):
        """Test setting invalid working directory"""
        with pytest.raises(ValueError):
            self.executor.set_working_directory("/nonexistent/directory")

    @patch('subprocess.run')
    def test_execute_single_command_success(self, mock_run):
        """Test successful command execution"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = self.executor._execute_single_command("echo hello")

        assert result["success"] == True
        assert result["return_code"] == 0
        assert result["stdout"] == "output"
        assert result["stderr"] == ""
        assert result["timed_out"] == False

        # Check subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["shell"] == True
        assert call_args[1]["cwd"] == self.executor.working_directory

    @patch('subprocess.run')
    def test_execute_single_command_failure(self, mock_run):
        """Test failed command execution"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "error message"
        mock_run.return_value = mock_process

        result = self.executor._execute_single_command("invalid_command")

        assert result["success"] == False
        assert result["return_code"] == 1
        assert result["stdout"] == ""
        assert result["stderr"] == "error message"

    @patch('subprocess.run')
    def test_execute_single_command_timeout(self, mock_run):
        """Test command execution timeout"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("cmd", 30)

        result = self.executor._execute_single_command("slow_command")

        assert result["success"] == False
        assert result["return_code"] == -1
        assert result["timed_out"] == True
        assert "timed out" in result["stderr"].lower()

    @patch('subprocess.run')
    def test_execute_single_command_exception(self, mock_run):
        """Test command execution with general exception"""
        mock_run.side_effect = Exception("System error")

        result = self.executor._execute_single_command("problematic_command")

        assert result["success"] == False
        assert result["return_code"] == -1
        assert result["timed_out"] == False
        assert "System error" in result["stderr"]

    def test_execute_commands_sequence(self):
        """Test executing multiple commands in sequence"""
        commands = ["echo first", "echo second"]
        explanations = ["First command", "Second command"]

        with patch.object(self.executor, '_execute_single_command') as mock_execute:
            mock_execute.side_effect = [
                {
                    "return_code": 0,
                    "stdout": "first output",
                    "stderr": "",
                    "success": True,
                    "timed_out": False
                },
                {
                    "return_code": 0,
                    "stdout": "second output",
                    "stderr": "",
                    "success": True,
                    "timed_out": False
                }
            ]

            result = self.executor.execute_commands(commands, explanations)

            assert result["total_commands"] == 2
            assert result["executed_commands"] == 2
            assert result["all_successful"] == True
            assert len(result["results"]) == 2

            # Check both commands were executed
            assert mock_execute.call_count == 2

    def test_execute_commands_with_failure(self):
        """Test executing commands where one fails"""
        commands = ["echo success", "invalid_command"]
        explanations = ["Success command", "Failure command"]

        with patch.object(self.executor, '_execute_single_command') as mock_execute:
            mock_execute.side_effect = [
                {
                    "return_code": 0,
                    "stdout": "success",
                    "stderr": "",
                    "success": True,
                    "timed_out": False
                },
                {
                    "return_code": 1,
                    "stdout": "",
                    "stderr": "command not found",
                    "success": False,
                    "timed_out": False
                }
            ]

            result = self.executor.execute_commands(commands, explanations)

            assert result["total_commands"] == 2
            assert result["executed_commands"] == 2
            assert result["all_successful"] == False

            # Check results
            assert result["results"][0]["success"] == True
            assert result["results"][1]["success"] == False

    @patch('subprocess.run')
    def test_test_command_success(self, mock_run):
        """Test command testing for success"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = self.executor.test_command("echo")

        assert result == True
        mock_run.assert_called_with("which echo", shell=True, capture_output=True, text=True)

    @patch('subprocess.run')
    def test_test_command_failure(self, mock_run):
        """Test command testing for failure"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        result = self.executor.test_command("nonexistent_command")

        assert result == False

    def test_is_critical_failure(self):
        """Test critical failure detection"""
        # For now, this always returns False (non-critical)
        assert self.executor._is_critical_failure("any_command", {"return_code": 1}) == False
        assert self.executor._is_critical_failure("any_command", {"return_code": 0}) == False
