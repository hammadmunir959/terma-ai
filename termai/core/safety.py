"""Safety checker for bash commands"""

import re
from typing import List, Dict, Any, Tuple


class SafetyChecker:
    """Check commands for safety before execution"""

    def __init__(self):
        """Initialize safety patterns"""
        self.dangerous_patterns = self._get_dangerous_patterns()
        self.warning_patterns = self._get_warning_patterns()

    def check_commands(self, commands: List[str]) -> Dict[str, Any]:
        """
        Check a list of commands for safety issues

        Args:
            commands: List of bash commands to check

        Returns:
            Dict with safety status and details
        """
        risky_commands = []
        warnings = []
        safe_commands = []

        for i, cmd in enumerate(commands):
            is_risky, risk_reason = self._is_command_risky(cmd)
            has_warning, warning_msg = self._has_command_warning(cmd)

            if is_risky:
                risk_score = self._calculate_risk_score(cmd)
                risky_commands.append({
                    "index": i,
                    "command": cmd,
                    "reason": risk_reason,
                    "risk_level": self._get_risk_level(cmd),
                    "risk_score": risk_score
                })
            else:
                safe_commands.append(cmd)
                if has_warning:
                    warnings.append({
                        "index": i,
                        "command": cmd,
                        "warning": warning_msg
                    })

        return {
            "safe": len(risky_commands) == 0,
            "safe_commands": safe_commands,
            "risky_commands": risky_commands,  # Changed from blocked_commands
            "warnings": warnings,
            "total_commands": len(commands),
            "has_risky": len(risky_commands) > 0
        }

    def _is_command_risky(self, command: str) -> Tuple[bool, str]:
        """Check if a command is risky (requires extra confirmation)"""
        for pattern, reason in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True, reason
        return False, ""

    def _calculate_risk_score(self, command: str) -> int:
        """Calculate risk score from 1-5 for a command"""
        # Level 5 - System destruction
        level5_patterns = [
            r'\brm\s+-rf\s+/',
            r'\bdd\s+if=/dev/zero',
            r'\bmkfs\b',
            r'\bfdisk\b',
            r'\bparted\b',
            r'\bkill\s+-9\s+-1',
        ]
        
        # Level 4 - Critical system modification
        level4_patterns = [
            r'>\s*/etc/',
            r'>\s*/boot/',
            r'>\s*/bin/',
            r'\bchmod\s+777\s+-R\s+/',
            r'\bchown\s+root\s+/',
        ]
        
        # Level 3 - System modification with sudo
        level3_patterns = [
            r'\bsudo\b',
            r'\biptables\s+-F',
            r'\bchmod\s+777\s+-R\b',
        ]
        
        # Level 2 - Potentially risky operations
        level2_patterns = [
            r'\brm\s+-rf\b',
            r'\bchmod\s+-R\b',
            r'\bchown\s+-R\b',
        ]
        
        # Level 1 - Safe read operations (default)
        
        for pattern in level5_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return 5
        
        for pattern in level4_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return 4
        
        for pattern in level3_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return 3
        
        for pattern in level2_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return 2
        
        # Check if it's a read-only command
        read_only_patterns = [r'\bls\b', r'\bcat\b', r'\bfind\b', r'\bgrep\b', r'\bpwd\b', r'\bdf\b', r'\bdu\b']
        if any(re.search(pattern, command, re.IGNORECASE) for pattern in read_only_patterns):
            return 1
        
        return 2  # Default to level 2 for unknown commands

    def _get_risk_level(self, command: str) -> str:
        """Get the risk level category of a command"""
        score = self._calculate_risk_score(command)
        
        if score >= 5:
            return "CRITICAL"
        elif score >= 4:
            return "HIGH"
        elif score >= 3:
            return "MEDIUM-HIGH"
        elif score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def analyze_impact(self, command: str) -> Dict[str, Any]:
        """Analyze the potential impact of a command"""
        risk_score = self._calculate_risk_score(command)
        
        impact = {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(command),
            "potential_effects": [],
            "safer_alternatives": []
        }
        
        if risk_score >= 5:
            impact["potential_effects"] = [
                "System destruction",
                "Data loss",
                "Irreversible changes",
                "System may become unbootable"
            ]
        elif risk_score >= 4:
            impact["potential_effects"] = [
                "System configuration changes",
                "Security implications",
                "May require system recovery"
            ]
        elif risk_score >= 3:
            impact["potential_effects"] = [
                "Requires elevated privileges",
                "May modify system files",
                "Could affect system stability"
            ]
        
        # Get safer alternatives
        impact["safer_alternatives"] = self.suggest_alternatives(command)
        
        return impact

    def _has_command_warning(self, command: str) -> Tuple[bool, str]:
        """Check if a command has warnings"""
        for pattern, warning in self.warning_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True, warning
        return False, ""

    def _get_dangerous_patterns(self) -> List[Tuple[str, str]]:
        """Get patterns for dangerous commands that should be blocked"""
        return [
            # File system destruction
            (r'\brm\s+-rf\s+/', "Dangerous: 'rm -rf /' can destroy entire system"),
            (r'\brm\s+-rf\s+\*', "Dangerous: 'rm -rf *' can delete all files"),
            (r'\bdd\s+if=/dev/zero', "Dangerous: 'dd if=/dev/zero' can overwrite disks"),

            # Privilege escalation
            (r'\bsudo\b', "Blocked: sudo commands require manual execution"),
            (r'\bsu\b', "Blocked: privilege escalation not allowed"),

            # System formatting
            (r'\bmkfs\b', "Dangerous: filesystem formatting can destroy data"),
            (r'\bfdisk\b', "Dangerous: disk partitioning can destroy data"),
            (r'\bparted\b', "Dangerous: partition editing can destroy data"),

            # Dangerous permissions
            (r'\bchmod\s+777\s+-R\b', "Dangerous: recursive 777 permissions are insecure"),
            (r'\bchown\s+root\b', "Dangerous: changing ownership to root"),

            # System file editing
            (r'>\s*/etc/', "Blocked: modifying system configuration files"),
            (r'>\s*/boot/', "Blocked: modifying boot files"),
            (r'>\s*/bin/', "Blocked: modifying system binaries"),
            (r'>\s*/usr/bin/', "Blocked: modifying system binaries"),

            # Network dangerous
            (r'\biptables\s+-F', "Dangerous: flushing firewall rules"),
            (r'\biptables\s+-X', "Dangerous: deleting firewall rules"),

            # Process killing
            (r'\bkill\s+-9\s+-1', "Dangerous: killing all processes"),
            (r'\bkillall\s+-9', "Dangerous: force killing all instances"),
        ]

    def _get_warning_patterns(self) -> List[Tuple[str, str]]:
        """Get patterns for commands that should have warnings"""
        return [
            # Recursive operations
            (r'\bchmod\s+-R\b', "Warning: recursive permission changes can be dangerous"),
            (r'\bchown\s+-R\b', "Warning: recursive ownership changes can be dangerous"),

            # Large file operations
            (r'\bgrep\s+-r\b', "Warning: recursive grep on large directories may be slow"),
            (r'\bfind\s+/\b', "Warning: searching from root may take a long time"),

            # Network operations
            (r'\bwget\b', "Warning: downloading files from internet"),
            (r'\bcurl\b', "Warning: network requests can be slow or fail"),

            # Package management (might need sudo)
            (r'\bapt\b', "Warning: package management may require privileges"),
            (r'\byum\b', "Warning: package management may require privileges"),
            (r'\bdnf\b', "Warning: package management may require privileges"),
            (r'\bpacman\b', "Warning: package management may require privileges"),
        ]

    def suggest_alternatives(self, dangerous_command: str) -> List[str]:
        """Suggest safer alternatives for dangerous commands"""
        suggestions = []

        if 'rm -rf /' in dangerous_command:
            suggestions.extend([
                "find . -name 'pattern' -type f -delete  # Delete specific files",
                "du -sh *  # Check disk usage instead",
                "df -h  # Check disk space"
            ])

        elif 'sudo' in dangerous_command:
            suggestions.append("# This command requires manual execution with sudo")

        elif 'chmod 777' in dangerous_command:
            suggestions.extend([
                "chmod 644 file  # Read/write for owner, read for others",
                "chmod 755 file  # Execute for owner, read/execute for others"
            ])

        elif 'mkfs' in dangerous_command:
            suggestions.extend([
                "lsblk  # List block devices",
                "df -h  # Check mounted filesystems"
            ])

        return suggestions if suggestions else ["# No safe alternatives available"]
