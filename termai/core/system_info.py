"""System Information Collector for Terma AI

Automatically collects comprehensive system information to help AI
generate more accurate and context-aware commands.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
try:
    import distro
except ImportError:
    distro = None


class SystemInfoCollector:
    """Collects comprehensive system information"""
    
    def __init__(self):
        self.info = {}
        self._collect_all()
    
    def _collect_all(self):
        """Collect all system information"""
        self.info = {
            "os": self._get_os_info(),
            "shell": self._get_shell_info(),
            "package_manager": self._detect_package_manager(),
            "python": self._get_python_info(),
            "user": self._get_user_info(),
            "paths": self._get_path_info(),
            "environment": self._get_environment_info(),
            "capabilities": self._get_capabilities(),
        }
    
    def _get_os_info(self) -> Dict[str, Any]:
        """Get operating system information"""
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            
            # Get distribution info for Linux
            dist_info = {}
            if system == "Linux":
                try:
                    if distro:
                        dist_info = {
                            "distribution": distro.name(pretty=True),
                            "id": distro.id(),
                            "version": distro.version(),
                            "codename": distro.codename(),
                        }
                    else:
                        # Fallback if distro library not available
                        if os.path.exists("/etc/os-release"):
                            with open("/etc/os-release") as f:
                                for line in f:
                                    if "PRETTY_NAME" in line:
                                        dist_info["distribution"] = line.split("=")[1].strip().strip('"')
                except:
                    # Fallback if distro library fails
                    if os.path.exists("/etc/os-release"):
                        with open("/etc/os-release") as f:
                            for line in f:
                                if "PRETTY_NAME" in line:
                                    dist_info["distribution"] = line.split("=")[1].strip().strip('"')
            
            return {
                "system": system,
                "release": release,
                "version": version,
                "machine": machine,
                "processor": processor,
                **dist_info,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_shell_info(self) -> Dict[str, Any]:
        """Get shell information"""
        shell_info = {
            "current_shell": os.environ.get("SHELL", "unknown"),
            "shell_name": "unknown",
            "shell_version": "unknown",
        }
        
        shell_path = shell_info["current_shell"]
        if shell_path:
            shell_name = Path(shell_path).name
            shell_info["shell_name"] = shell_name
            
            # Get shell version
            try:
                if shell_name == "bash":
                    result = subprocess.run(
                        ["bash", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        shell_info["shell_version"] = result.stdout.split("\n")[0]
                elif shell_name == "zsh":
                    result = subprocess.run(
                        ["zsh", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        shell_info["shell_version"] = result.stdout.strip()
                elif shell_name == "fish":
                    result = subprocess.run(
                        ["fish", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        shell_info["shell_version"] = result.stdout.strip()
            except:
                pass
        
        # Check if running in specific shell environments
        shell_info["is_wsl"] = "microsoft" in platform.release().lower() if platform.system() == "Linux" else False
        shell_info["is_docker"] = os.path.exists("/.dockerenv")
        shell_info["is_container"] = os.path.exists("/.dockerenv") or os.path.exists("/proc/1/cgroup")
        
        return shell_info
    
    def _detect_package_manager(self) -> Dict[str, Any]:
        """Detect available package managers"""
        package_managers = {
            "apt": {"available": False, "version": None},
            "yum": {"available": False, "version": None},
            "dnf": {"available": False, "version": None},
            "pacman": {"available": False, "version": None},
            "zypper": {"available": False, "version": None},
            "apk": {"available": False, "version": None},
            "brew": {"available": False, "version": None},
        }
        
        for pm in package_managers.keys():
            if shutil.which(pm):
                package_managers[pm]["available"] = True
                try:
                    result = subprocess.run(
                        [pm, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        package_managers[pm]["version"] = result.stdout.split("\n")[0].strip()
                except:
                    pass
        
        # Determine primary package manager
        primary = None
        if package_managers["apt"]["available"]:
            primary = "apt"
        elif package_managers["dnf"]["available"]:
            primary = "dnf"
        elif package_managers["yum"]["available"]:
            primary = "yum"
        elif package_managers["pacman"]["available"]:
            primary = "pacman"
        elif package_managers["zypper"]["available"]:
            primary = "zypper"
        elif package_managers["apk"]["available"]:
            primary = "apk"
        elif package_managers["brew"]["available"]:
            primary = "brew"
        
        return {
            "primary": primary,
            "available": {k: v["available"] for k, v in package_managers.items()},
            "versions": {k: v["version"] for k, v in package_managers.items() if v["version"]},
        }
    
    def _get_python_info(self) -> Dict[str, Any]:
        """Get Python information"""
        return {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "path": sys.path[:3],  # First 3 paths
        }
    
    def _get_user_info(self) -> Dict[str, Any]:
        """Get user information"""
        return {
            "username": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
            "home": os.path.expanduser("~"),
            "uid": os.getuid() if hasattr(os, "getuid") else None,
            "gid": os.getgid() if hasattr(os, "getgid") else None,
            "is_root": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
        }
    
    def _get_path_info(self) -> Dict[str, Any]:
        """Get important path information"""
        return {
            "current_directory": os.getcwd(),
            "home": os.path.expanduser("~"),
            "temp": os.path.expanduser("~/.cache") if os.path.exists(os.path.expanduser("~/.cache")) else "/tmp",
            "config": os.path.expanduser("~/.config"),
        }
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "lang": os.getenv("LANG", "unknown"),
            "timezone": os.getenv("TZ", "unknown"),
            "editor": os.getenv("EDITOR") or os.getenv("VISUAL", "unknown"),
            "pager": os.getenv("PAGER", "less"),
        }
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities"""
        capabilities = {
            "sudo": shutil.which("sudo") is not None,
            "docker": shutil.which("docker") is not None,
            "git": shutil.which("git") is not None,
            "node": shutil.which("node") is not None,
            "npm": shutil.which("npm") is not None,
            "python3": shutil.which("python3") is not None,
            "pip3": shutil.which("pip3") is not None,
        }
        
        # Check versions for available tools
        versions = {}
        for tool in ["git", "docker", "node", "npm"]:
            if capabilities.get(tool):
                try:
                    result = subprocess.run(
                        [tool, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        versions[tool] = result.stdout.split("\n")[0].strip()
                except:
                    pass
        
        return {
            **capabilities,
            "versions": versions,
        }
    
    def get_summary(self) -> str:
        """Get a formatted summary of system information"""
        lines = []
        
        # OS Info
        os_info = self.info.get("os", {})
        if os_info.get("distribution"):
            lines.append(f"OS: {os_info['distribution']} ({os_info.get('version', '')})")
        else:
            lines.append(f"OS: {os_info.get('system', 'unknown')} {os_info.get('release', '')}")
        
        # Shell
        shell_info = self.info.get("shell", {})
        lines.append(f"Shell: {shell_info.get('shell_name', 'unknown')} ({shell_info.get('shell_version', 'unknown')})")
        
        # Package Manager
        pm_info = self.info.get("package_manager", {})
        if pm_info.get("primary"):
            lines.append(f"Package Manager: {pm_info['primary']}")
        
        # Python
        python_info = self.info.get("python", {})
        lines.append(f"Python: {python_info.get('version', 'unknown')}")
        
        # User
        user_info = self.info.get("user", {})
        lines.append(f"User: {user_info.get('username', 'unknown')}")
        if user_info.get("is_root"):
            lines.append("⚠️ Running as root")
        
        # Capabilities
        caps = self.info.get("capabilities", {})
        available_tools = [tool for tool, avail in caps.items() if avail and tool not in ["versions"]]
        if available_tools:
            lines.append(f"Available tools: {', '.join(available_tools)}")
        
        return "\n".join(lines)
    
    def get_detailed_context(self) -> str:
        """Get detailed context string for LLM prompts"""
        context_parts = []
        
        # OS Context
        os_info = self.info.get("os", {})
        if os_info.get("distribution"):
            context_parts.append(f"Operating System: {os_info['distribution']} {os_info.get('version', '')}")
            if os_info.get("codename"):
                context_parts.append(f"OS Codename: {os_info['codename']}")
        else:
            context_parts.append(f"Operating System: {os_info.get('system', 'unknown')} {os_info.get('release', '')}")
        
        # Shell Context
        shell_info = self.info.get("shell", {})
        context_parts.append(f"Shell: {shell_info.get('shell_name', 'bash')} (path: {shell_info.get('current_shell', 'unknown')})")
        
        # Package Manager Context
        pm_info = self.info.get("package_manager", {})
        if pm_info.get("primary"):
            context_parts.append(f"Primary Package Manager: {pm_info['primary']}")
            available_pms = [pm for pm, avail in pm_info.get('available', {}).items() if avail]
            if len(available_pms) > 1:
                context_parts.append(f"Other available package managers: {', '.join(available_pms)}")
        
        # Python Context
        python_info = self.info.get("python", {})
        context_parts.append(f"Python: {python_info.get('version', 'unknown')} ({python_info.get('implementation', 'CPython')})")
        
        # User Context
        user_info = self.info.get("user", {})
        context_parts.append(f"User: {user_info.get('username', 'unknown')}")
        context_parts.append(f"Home Directory: {user_info.get('home', 'unknown')}")
        if user_info.get("is_root"):
            context_parts.append("⚠️ WARNING: Running as root user - be extra careful with commands")
        
        # Environment Context
        env_info = self.info.get("environment", {})
        if env_info.get("editor") != "unknown":
            context_parts.append(f"Default Editor: {env_info.get('editor', 'unknown')}")
        
        # Capabilities Context
        caps = self.info.get("capabilities", {})
        available_tools = []
        for tool in ["git", "docker", "node", "npm", "sudo"]:
            if caps.get(tool):
                version = caps.get("versions", {}).get(tool, "")
                if version:
                    available_tools.append(f"{tool} ({version})")
                else:
                    available_tools.append(tool)
        
        if available_tools:
            context_parts.append(f"Available Development Tools: {', '.join(available_tools)}")
        
        # Special Environments
        shell_info = self.info.get("shell", {})
        if shell_info.get("is_wsl"):
            context_parts.append("⚠️ Running in WSL (Windows Subsystem for Linux)")
        if shell_info.get("is_docker"):
            context_parts.append("⚠️ Running in Docker container")
        
        return "\n".join(context_parts)
    
    def get_dict(self) -> Dict[str, Any]:
        """Get all system information as a dictionary"""
        return self.info.copy()

