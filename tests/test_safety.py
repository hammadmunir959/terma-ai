"""Tests for safety checker"""

import pytest
from termai.core.safety import SafetyChecker


class TestSafetyChecker:
    """Test the safety checker functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.checker = SafetyChecker()

    def test_safe_commands_pass(self):
        """Test that safe commands pass safety checks"""
        safe_commands = [
            "ls -la",
            "pwd",
            "echo hello",
            "df -h",
            "ps aux",
            "find . -name '*.txt'",
            "grep 'pattern' file.txt"
        ]

        result = self.checker.check_commands(safe_commands)

        assert result["safe"] == True
        assert len(result["safe_commands"]) == len(safe_commands)
        assert len(result.get("risky_commands", [])) == 0

    def test_dangerous_commands_flagged_as_risky(self):
        """Test that dangerous commands are flagged as risky (not blocked)"""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
            "> /etc/passwd",
            "chmod 777 -R /",
            "chown root:root /etc/shadow"
        ]

        result = self.checker.check_commands(dangerous_commands)

        assert result["safe"] == False
        assert result["has_risky"] == True
        assert len(result["risky_commands"]) == len(dangerous_commands)
        assert len(result["safe_commands"]) == 0

        # Check that each command has a reason and risk level
        for risky in result["risky_commands"]:
            assert "reason" in risky
            assert "risk_level" in risky
            assert len(risky["reason"]) > 0
            assert risky["risk_level"] in ["CRITICAL", "HIGH", "MEDIUM"]

    def test_warning_commands(self):
        """Test that commands with warnings are flagged"""
        warning_commands = [
            "chmod -R 755 directory",
            "chown -R user:group directory",
            "apt update",  # Package manager
            "yum install package",
            "wget http://example.com/file",
            "curl http://example.com"
        ]

        result = self.checker.check_commands(warning_commands)

        assert result["safe"] == True  # Warnings don't block execution
        assert len(result["warnings"]) > 0

    def test_mixed_commands(self):
        """Test mix of safe, warning, and dangerous commands"""
        mixed_commands = [
            "ls -la",           # Safe
            "chmod -R 755 .",   # Warning
            "rm -rf /",         # Dangerous
            "pwd",              # Safe
            "sudo apt update"   # Dangerous (sudo)
        ]

        result = self.checker.check_commands(mixed_commands)

        assert result["safe"] == False
        assert result["has_risky"] == True
        assert len(result["risky_commands"]) == 2  # rm -rf / and sudo
        assert len(result["safe_commands"]) == 3     # ls, chmod -R, pwd (warnings don't block)
        assert len(result["warnings"]) == 1          # chmod -R

    def test_alternatives_suggestions(self):
        """Test that alternatives are suggested for dangerous commands"""
        dangerous_commands = [
            "rm -rf /",
            "sudo command",
            "mkfs /dev/sda"
        ]

        alternatives = []
        for cmd in dangerous_commands:
            alternatives.extend(self.checker.suggest_alternatives(cmd))

        assert len(alternatives) > 0
        assert any("find" in alt for alt in alternatives)
        assert any("du" in alt for alt in alternatives)

    def test_empty_command_list(self):
        """Test handling of empty command list"""
        result = self.checker.check_commands([])

        assert result["safe"] == True
        assert len(result["safe_commands"]) == 0
        assert len(result.get("risky_commands", [])) == 0
        assert len(result["warnings"]) == 0
