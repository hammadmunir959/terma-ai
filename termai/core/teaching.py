"""Teaching mode and command explanations"""

from typing import List, Dict, Any, Optional
from .llm import LLMClient
from .safety import SafetyChecker


class TeachingMode:
    """Provide explanations and teaching for commands"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize teaching mode"""
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()

    def explain_command(self, command: str) -> Dict[str, Any]:
        """
        Explain what a command does in simple terms
        
        Args:
            command: Bash command to explain
            
        Returns:
            Explanation dictionary
        """
        explanation_prompt = f"""Explain this Linux command in simple, beginner-friendly terms: "{command}"

Provide:
1. What the command does
2. What each part means
3. Why someone might use it
4. Any important warnings

Keep it clear and educational."""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a Linux teacher helping beginners understand commands."},
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            explanation = response.choices[0].message.content
            
            # Get safety analysis
            impact = self.safety_checker.analyze_impact(command)
            
            return {
                "command": command,
                "explanation": explanation,
                "risk_score": impact["risk_score"],
                "risk_level": impact["risk_level"],
                "potential_effects": impact["potential_effects"],
                "safer_alternatives": impact["safer_alternatives"]
            }
            
        except Exception as e:
            return {
                "command": command,
                "explanation": f"Could not generate explanation: {str(e)}",
                "error": str(e)
            }

    def explain_why(self, command: str, user_request: str) -> str:
        """
        Explain why a specific command was chosen for a user request
        
        Args:
            command: The command to explain
            user_request: Original user request
            
        Returns:
            Explanation text
        """
        prompt = f"""User requested: "{user_request}"
I generated this command: "{command}"

Explain why this command is appropriate for the user's request. Be clear and educational."""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a Linux teacher explaining command choices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"

    def suggest_safer_way(self, command: str) -> Dict[str, Any]:
        """
        Suggest safer alternatives to a command
        
        Args:
            command: Command to find alternatives for
            
        Returns:
            Dictionary with safer alternatives
        """
        impact = self.safety_checker.analyze_impact(command)
        
        prompt = f"""This command might be risky: "{command}"

Suggest safer alternatives that achieve similar goals. Explain why each alternative is safer."""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a Linux safety advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            ai_suggestions = response.choices[0].message.content
            
            return {
                "original_command": command,
                "risk_score": impact["risk_score"],
                "ai_suggestions": ai_suggestions,
                "pattern_based_alternatives": impact["safer_alternatives"]
            }
            
        except Exception as e:
            return {
                "original_command": command,
                "error": str(e),
                "pattern_based_alternatives": impact["safer_alternatives"]
            }

    def break_down_steps(self, command: str) -> List[Dict[str, str]]:
        """
        Break down a complex command into understandable steps
        
        Args:
            command: Command to break down
            
        Returns:
            List of step explanations
        """
        prompt = f"""Break down this Linux command into simple steps: "{command}"

For each part of the command, explain what it does."""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a Linux teacher breaking down commands."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            explanation = response.choices[0].message.content
            
            # Simple parsing - split by numbered steps
            steps = []
            lines = explanation.split('\n')
            current_step = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if it's a step header
                if line[0].isdigit() or line.startswith('-') or line.startswith('*'):
                    if current_step:
                        steps.append(current_step)
                    current_step = {"step": line, "explanation": ""}
                elif current_step:
                    current_step["explanation"] += line + " "
            
            if current_step:
                steps.append(current_step)
            
            if not steps:
                steps = [{"step": "1", "explanation": explanation}]
            
            return steps
            
        except Exception as e:
            return [{"step": "1", "explanation": f"Could not break down command: {str(e)}"}]
