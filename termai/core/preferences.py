"""User preferences and behavior configuration"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Preferences:
    """Manage user preferences for Terma AI"""

    DEFAULT_PREFS = {
        "package_manager": "apt",  # apt, yum, dnf, pacman
        "editor": "nano",  # nano, vim, code, etc.
        "safety_mode": "confirm",  # confirm, strict, permissive
        "verbosity": "normal",  # low, normal, high
        "teaching_mode": False,  # Show explanations
        "default_confirm": True,  # Default confirmation behavior
        "preferred_shell": "bash",  # bash, zsh, fish
    }

    def __init__(self, prefs_file: Optional[str] = None):
        """Initialize preferences manager"""
        if prefs_file is None:
            # Use ~/.termai/preferences.yaml
            home = Path.home()
            prefs_dir = home / ".termai"
            prefs_dir.mkdir(exist_ok=True)
            prefs_file = str(prefs_dir / "preferences.yaml")
        
        self.prefs_file = prefs_file
        self.prefs = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences from file"""
        if os.path.exists(self.prefs_file):
            try:
                with open(self.prefs_file, 'r') as f:
                    loaded = yaml.safe_load(f) or {}
                    # Merge with defaults
                    prefs = self.DEFAULT_PREFS.copy()
                    prefs.update(loaded)
                    return prefs
            except Exception as e:
                print(f"Warning: Could not load preferences: {e}")
                return self.DEFAULT_PREFS.copy()
        else:
            # Create default preferences file
            self._save_preferences(self.DEFAULT_PREFS.copy())
            return self.DEFAULT_PREFS.copy()

    def _save_preferences(self, prefs: Dict[str, Any]):
        """Save preferences to file"""
        try:
            with open(self.prefs_file, 'w') as f:
                yaml.dump(prefs, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise Exception(f"Failed to save preferences: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value"""
        return self.prefs.get(key, default)

    def set(self, key: str, value: Any):
        """Set a preference value"""
        if key not in self.DEFAULT_PREFS:
            raise ValueError(f"Unknown preference: {key}")
        
        self.prefs[key] = value
        self._save_preferences(self.prefs)

    def list_all(self) -> Dict[str, Any]:
        """Get all preferences"""
        return self.prefs.copy()

    def reset(self):
        """Reset to default preferences"""
        self.prefs = self.DEFAULT_PREFS.copy()
        self._save_preferences(self.prefs)

    def get_system_prompt_addition(self) -> str:
        """Get additional system prompt text based on preferences"""
        additions = []
        
        if self.prefs.get("package_manager"):
            pm = self.prefs["package_manager"]
            additions.append(f"User prefers {pm} as package manager.")
        
        if self.prefs.get("editor"):
            editor = self.prefs["editor"]
            additions.append(f"User prefers {editor} as text editor.")
        
        if self.prefs.get("teaching_mode"):
            additions.append("User wants detailed explanations and teaching mode enabled.")
        
        if self.prefs.get("verbosity") == "high":
            additions.append("User prefers verbose output with detailed explanations.")
        elif self.prefs.get("verbosity") == "low":
            additions.append("User prefers minimal output.")
        
        return " ".join(additions) if additions else ""
