"""File helper utilities for suggesting similar files"""

import os
import re
from pathlib import Path
from typing import List, Optional
from difflib import get_close_matches


def extract_filename_from_error(error_message: str) -> Optional[str]:
    """Extract filename from 'No such file or directory' error"""
    # Pattern: "cat: filename: No such file or directory"
    patterns = [
        r':\s*([^:]+):\s*No such file or directory',
        r':\s*([^:]+):\s*cannot open',
        r'No such file or directory:\s*([^\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def find_similar_files(filename: str, directory: str = ".", max_results: int = 5) -> List[str]:
    """Find similar files in the directory using fuzzy matching"""
    try:
        path = Path(directory)
        if not path.exists():
            return []
        
        # Get all files in directory
        all_files = []
        for item in path.iterdir():
            if item.is_file():
                all_files.append(item.name)
            elif item.is_dir():
                all_files.append(item.name + "/")
        
        if not all_files:
            return []
        
        # Use fuzzy matching to find similar files
        # Normalize filename for comparison
        normalized_filename = filename.lower()
        similar = get_close_matches(
            normalized_filename,
            [f.lower() for f in all_files],
            n=max_results,
            cutoff=0.3  # Minimum similarity threshold
        )
        
        # Map back to original filenames (preserve case)
        result = []
        for sim in similar:
            # Find original filename with case preserved
            for orig_file in all_files:
                if orig_file.lower() == sim:
                    result.append(orig_file)
                    break
        
        return result
    
    except Exception:
        return []


def suggest_files_for_error(error_message: str, directory: str = ".") -> Optional[List[str]]:
    """Suggest similar files when a file not found error occurs"""
    filename = extract_filename_from_error(error_message)
    if not filename:
        return None
    
    similar_files = find_similar_files(filename, directory)
    return similar_files if similar_files else None


def find_case_insensitive_match(filename: str, directory: str = ".") -> Optional[str]:
    """Find a case-insensitive or fuzzy match for a filename in the directory"""
    try:
        path = Path(directory).resolve()
        if not path.exists() or not path.is_dir():
            return None
        
        # Normalize filename
        filename_clean = filename.strip().lstrip('./')
        filename_lower = filename_clean.lower()
        
        # First try exact case-insensitive match
        for item in path.iterdir():
            item_name_lower = item.name.lower()
            if item_name_lower == filename_lower:
                if item.is_file():
                    return item.name
                elif item.is_dir():
                    return item.name + "/"
        
        # If no exact match, try fuzzy matching for similar filenames
        all_files = []
        for item in path.iterdir():
            if item.is_file():
                all_files.append(item.name)
            elif item.is_dir():
                all_files.append(item.name + "/")
        
        if all_files:
            # Use fuzzy matching
            similar = get_close_matches(
                filename_lower,
                [f.lower() for f in all_files],
                n=1,
                cutoff=0.6  # Higher threshold for auto-correction
            )
            
            if similar:
                # Find original filename with case preserved
                for orig_file in all_files:
                    if orig_file.lower() == similar[0]:
                        return orig_file
        
        return None
    
    except Exception:
        return None


def correct_filename_in_command(command: str, directory: str = ".") -> tuple[str, bool]:
    """
    Correct filenames in a command using case-insensitive matching.
    
    Returns:
        (corrected_command, was_corrected)
    """
    import re
    import shlex
    
    corrected_command = command
    was_corrected = False
    
    try:
        # Try to parse command into parts
        # Handle commands like: cat file, ls -la file, grep pattern file
        parts = shlex.split(command)
        
        if len(parts) < 2:
            return command, False
        
        # Check each part (skip command itself and flags)
        for i, part in enumerate(parts[1:], 1):
            # Skip flags and options
            if part.startswith('-'):
                continue
            
            # Skip if it's clearly not a file path (has special chars)
            if any(char in part for char in ['|', '&', ';', '>', '<', '(', ')', '$', '*', '?', '[']):
                continue
            
            # Check if it looks like a file path (has extension or is a relative path)
            is_likely_file = (
                '.' in part or  # Has extension
                '/' in part or  # Has path separator
                part.endswith('/')  # Is a directory reference
            )
            
            if not is_likely_file and len(parts) > 2:
                # Might be an argument, not a file - skip
                continue
            
            # Try to find case-insensitive match
            corrected_file = find_case_insensitive_match(part, directory)
            if corrected_file and corrected_file != part:
                # Replace in original command (preserve quotes if any)
                corrected_command = corrected_command.replace(part, corrected_file, 1)
                was_corrected = True
                break  # Only correct first match to avoid over-correction
    
    except (ValueError, Exception):
        # If parsing fails, try regex fallback
        # Pattern: command followed by filename
        pattern = r'\b(cat|less|more|head|tail|grep|sed|awk|find|ls|cd|mv|cp|rm|chmod|chown|touch|nano|vim|vi|code)\s+([^\s|&;<>()$]+)'
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            potential_file = match.group(2).strip()
            # Remove quotes if present
            if potential_file.startswith('"') or potential_file.startswith("'"):
                potential_file = potential_file[1:-1]
            
            corrected_file = find_case_insensitive_match(potential_file, directory)
            if corrected_file and corrected_file != potential_file:
                corrected_command = command.replace(potential_file, corrected_file, 1)
                was_corrected = True
    
    return corrected_command, was_corrected

