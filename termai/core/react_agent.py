"""ReAct (Reasoning + Acting) Agent for Terma AI

Implements a fully agentic system that:
1. Creates a todo list based on the goal
2. Observes the current state
3. Reasons about what needs to be done
4. Plans the next action from todo list
5. Acts (executes commands)
6. Updates todo list based on observations
7. Loops until goal is achieved or determined impossible
"""

import json
import time
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from .llm import LLMClient
from .safety import SafetyChecker
from .executor import CommandExecutor
from .display import DisplayManager


class ReActAgent:
    """Fully agentic ReAct agent with todo list management"""

    def __init__(self, llm_client: Optional[LLMClient] = None, working_directory: Optional[str] = None):
        """Initialize the ReAct agent"""
        self.console = Console()
        self.llm_client = llm_client or LLMClient()
        self.safety_checker = SafetyChecker()
        self.executor = CommandExecutor(working_directory=working_directory)
        self.display = DisplayManager()
        
        # Agent state
        self.goal = ""
        self.todo_list: List[Dict[str, Any]] = []
        self.observation_history: List[Dict[str, Any]] = []
        self.action_history: List[Dict[str, Any]] = []
        self.reasoning_history: List[str] = []
        self.max_iterations = 7  # Default to 7, encourage 3-5
        self.current_iteration = 0

    def achieve_goal(
        self, 
        goal: str, 
        auto_confirm: bool = False,
        max_iterations: int = 7,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Achieve a goal using ReAct methodology with todo list
        
        Args:
            goal: Natural language description of the goal
            auto_confirm: Automatically confirm risky actions
            max_iterations: Maximum number of observe-reason-plan-act cycles (default: 7, encourage 3-5)
            verbose: Show detailed reasoning and observations
            
        Returns:
            Dict with goal achievement results
        """
        self.goal = goal
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.observation_history = []
        self.action_history = []
        self.reasoning_history = []
        self.todo_list = []
        
        # Initial observation
        initial_state = self._observe()
        self.observation_history.append({
            "iteration": 0,
            "state": initial_state,
            "type": "initial"
        })
        
        self.console.print(Panel(
            f"[bold blue]🤖 ReAct Agent[/bold blue]\n\n"
            f"[bold]Goal:[/bold] {goal}\n"
            f"[dim]Starting from: {self.executor.get_working_directory()}[/dim]\n"
            f"[dim]Max iterations: {max_iterations} (3-5 recommended for most goals)[/dim]",
            title="Goal Achievement",
            border_style="blue"
        ))
        
        if verbose:
            self.console.print(f"\n[bold cyan]📊 Initial Observation:[/bold cyan]")
            self._display_observation(initial_state)
        
        # Step 1: Create initial todo list
        self.console.print(f"\n[bold yellow]📝 Creating Todo List...[/bold yellow]")
        self.todo_list = self._create_todo_list(goal, initial_state)
        
        if verbose:
            self._display_todo_list()
        
        # Main ReAct loop
        goal_achieved = False
        goal_impossible = False
        final_reasoning = ""
        
        try:
            while self.current_iteration < self.max_iterations and not goal_achieved and not goal_impossible:
                self.current_iteration += 1
                
                if verbose:
                    self.console.print(f"\n[bold cyan]{'='*70}[/bold cyan]")
                    self.console.print(f"[bold cyan]🔄 Iteration {self.current_iteration}/{self.max_iterations}[/bold cyan]")
                
                # Step 1: OBSERVE - Get current state
                current_state = self._observe()
                self.observation_history.append({
                    "iteration": self.current_iteration,
                    "state": current_state,
                    "type": "before_action"
                })
                
                if verbose:
                    self.console.print(f"\n[bold magenta]👁️  Current Observation:[/bold magenta]")
                    self._display_observation(current_state)
                
                # Step 2: REASON - Analyze current state and todo list
                reasoning = self._reason(goal, current_state, self.todo_list, self.action_history)
                self.reasoning_history.append(reasoning)
                
                if verbose:
                    self.console.print(f"\n[bold yellow]💭 Reasoning:[/bold yellow]")
                    self.console.print(f"[dim]{reasoning.get('analysis', '')}[/dim]")
                
                # Check if goal is achieved
                if reasoning.get("goal_achieved", False):
                    goal_achieved = True
                    final_reasoning = reasoning.get("analysis", "")
                    if verbose:
                        self.console.print(f"\n[bold green]✅ Goal Achieved![/bold green]")
                    break
                
                # Check if goal is impossible
                if reasoning.get("goal_impossible", False):
                    goal_impossible = True
                    final_reasoning = reasoning.get("analysis", "")
                    if verbose:
                        self.console.print(f"\n[bold red]❌ Goal Determined Impossible[/bold red]")
                    break
                
                # Step 3: UPDATE TODO LIST - Based on new observations
                if reasoning.get("update_todo_list", False):
                    if verbose:
                        self.console.print(f"\n[bold blue]📋 Updating Todo List...[/bold blue]")
                    self.todo_list = self._update_todo_list(
                        goal, 
                        current_state, 
                        self.todo_list, 
                        reasoning
                    )
                    if verbose:
                        self._display_todo_list()
                
                # Step 4: PLAN - Decide on next action from todo list
                plan = self._plan(reasoning, current_state, self.todo_list)
                
                if verbose:
                    self.console.print(f"\n[bold blue]📋 Plan:[/bold blue]")
                    self.console.print(f"[cyan]Now I'm doing:[/cyan] {plan.get('current_action_description', '')}")
                    if plan.get("next_action_description"):
                        self.console.print(f"[dim]Next I'll do:[/dim] {plan.get('next_action_description', '')}")
                
                # Check if no action needed
                if plan.get("no_action_needed", False):
                    if verbose:
                        self.console.print(f"[yellow]⚠️  No action needed, continuing...[/yellow]")
                    continue
                
                actions = plan.get("actions", [])
                if not actions:
                    if verbose:
                        self.console.print(f"[yellow]⚠️  No actions planned, continuing...[/yellow]")
                    continue
                
                # Step 5: ACT - Execute the planned action(s)
                if verbose:
                    self.console.print(f"\n[bold green]⚡ Acting:[/bold green]")
                
                action_results = []
                for i, action in enumerate(actions, 1):
                    if verbose and len(actions) > 1:
                        self.console.print(f"\n[dim]Action {i}/{len(actions)}:[/dim]")
                    
                    action_result = self._act(action, auto_confirm, verbose)
                    action_results.append(action_result)
                    self.action_history.append({
                        "iteration": self.current_iteration,
                        "action": action,
                        "result": action_result
                    })
                    
                    # If action failed critically, break
                    if action_result.get("critical_failure", False):
                        if verbose:
                            self.console.print(f"[red]❌ Critical failure, stopping[/red]")
                        goal_impossible = True
                        break
                
                # Step 6: OBSERVE - Check the new state after action
                new_state = self._observe()
                self.observation_history.append({
                    "iteration": self.current_iteration,
                    "state": new_state,
                    "type": "after_action",
                    "actions_taken": actions
                })
                
                if verbose:
                    self.console.print(f"\n[bold magenta]👁️  Updated Observation:[/bold magenta]")
                    self._display_observation(new_state)
                
                # Mark completed todos
                self._mark_todo_completed(actions, action_results)
                
                # Small delay to prevent rapid-fire execution
                time.sleep(0.3)
        
        except KeyboardInterrupt:
            self.console.print(f"\n[yellow]⚠️  Interrupted by user[/yellow]")
            return {
                "goal": goal,
                "status": "interrupted",
                "iterations": self.current_iteration,
                "todo_list": self.todo_list,
                "observation_history": self.observation_history,
                "action_history": self.action_history,
                "reasoning_history": self.reasoning_history
            }
        
        # Generate natural language summary
        summary = self._generate_natural_language_summary(
            goal,
            goal_achieved,
            final_reasoning,
            self.todo_list,
            self.action_history
        )
        
        # Final summary
        return {
            "goal": goal,
            "status": "achieved" if goal_achieved else ("impossible" if goal_impossible else "max_iterations"),
            "iterations": self.current_iteration,
            "goal_achieved": goal_achieved,
            "final_reasoning": final_reasoning,
            "natural_language_summary": summary,
            "todo_list": self.todo_list,
            "observation_history": self.observation_history,
            "action_history": self.action_history,
            "reasoning_history": self.reasoning_history,
            "total_actions": len(self.action_history)
        }

    def _observe(self) -> Dict[str, Any]:
        """Observe the current state of the system - updated at each iteration"""
        working_dir = self.executor.get_working_directory()
        
        # Get file system state
        files = []
        dirs = []
        file_sizes = {}
        try:
            path = Path(working_dir)
            if path.exists() and path.is_dir():
                for item in sorted(path.iterdir()):
                    if item.is_file():
                        files.append(item.name)
                        try:
                            file_sizes[item.name] = item.stat().st_size
                        except:
                            pass
                    elif item.is_dir():
                        dirs.append(item.name)
        except Exception:
            pass
        
        # Get recent command outputs (last 5)
        recent_outputs = []
        if self.action_history:
            for action_result in self.action_history[-5:]:
                result = action_result.get("result", {})
                action = action_result.get("action", {})
                if result.get("stdout") or result.get("stderr"):
                    recent_outputs.append({
                        "command": action.get("command", ""),
                        "stdout": result.get("stdout", "")[:300],
                        "stderr": result.get("stderr", "")[:300],
                        "success": result.get("success", False)
                    })
        
        # Get completed todos count
        completed_todos = sum(1 for todo in self.todo_list if todo.get("completed", False))
        total_todos = len(self.todo_list)
        
        return {
            "working_directory": working_dir,
            "files": files[:30],  # Increased limit
            "directories": dirs[:15],
            "file_sizes": file_sizes,
            "recent_outputs": recent_outputs,
            "completed_todos": completed_todos,
            "total_todos": total_todos,
            "timestamp": time.time()
        }

    def _create_todo_list(self, goal: str, initial_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create initial todo list based on goal"""
        files = initial_state.get("files", [])
        dirs = initial_state.get("directories", [])
        
        context = f"Goal: {goal}\n\n"
        context += f"Current working directory: {initial_state.get('working_directory', '')}\n"
        context += f"Files: {', '.join(files[:15])}\n"
        context += f"Directories: {', '.join(dirs[:10])}\n"
        
        prompt = f"""You are a ReAct planning agent. Create a todo list to achieve this goal.

{context}

Create a structured todo list with specific, actionable items. Each item should be:
- Clear and specific
- In logical order
- Achievable with bash commands
- Not too granular (group related actions)

Return as JSON:
{{
  "todos": [
    {{
      "id": 1,
      "task": "Specific task description",
      "description": "What this task accomplishes",
      "priority": "high|medium|low",
      "dependencies": [],
      "estimated_commands": ["command1", "command2"]
    }}
  ],
  "estimated_iterations": 3-5
}}

Aim for 3-7 todos that can be completed in 3-5 iterations."""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a ReAct planning agent. Create structured todo lists for goal achievement."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            
            todos = result.get("todos", [])
            for todo in todos:
                todo["completed"] = False
            
            return todos
            
        except Exception as e:
            # Fallback todo list
            return [
                {
                    "id": 1,
                    "task": f"Achieve goal: {goal}",
                    "description": "Main goal",
                    "priority": "high",
                    "completed": False,
                    "dependencies": []
                }
            ]

    def _update_todo_list(
        self,
        goal: str,
        current_state: Dict[str, Any],
        current_todos: List[Dict[str, Any]],
        reasoning: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Update todo list based on new observations and reasoning"""
        
        completed = [t for t in current_todos if t.get("completed", False)]
        remaining = [t for t in current_todos if not t.get("completed", False)]
        
        context = f"Goal: {goal}\n\n"
        context += f"Current state:\n"
        context += f"- Files: {', '.join(current_state.get('files', [])[:15])}\n"
        context += f"- Completed todos: {len(completed)}/{len(current_todos)}\n"
        context += f"Reasoning: {reasoning.get('analysis', '')}\n"
        context += f"Remaining todos: {[t.get('task') for t in remaining]}\n"
        
        prompt = f"""Update the todo list based on current observations and reasoning.

{context}

You can:
- Mark todos as completed if they're done
- Add new todos if needed
- Remove todos that are no longer relevant
- Reorder todos based on dependencies
- Update priorities

Return as JSON:
{{
  "todos": [
    {{
      "id": 1,
      "task": "Task description",
      "description": "What this accomplishes",
      "priority": "high|medium|low",
      "completed": true/false,
      "dependencies": []
    }}
  ],
  "changes": "Brief description of what changed"
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a ReAct planning agent. Update todo lists based on observations."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            
            todos = result.get("todos", current_todos)
            
            # Preserve completion status if not specified
            for todo in todos:
                if "completed" not in todo:
                    # Try to match with existing todo
                    existing = next((t for t in current_todos if t.get("id") == todo.get("id")), None)
                    todo["completed"] = existing.get("completed", False) if existing else False
            
            return todos
            
        except Exception as e:
            # Return current todos if update fails
            return current_todos

    def _reason(
        self, 
        goal: str, 
        current_observation: Dict[str, Any],
        todo_list: List[Dict[str, Any]],
        action_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Reason about the current state and determine if goal is achieved"""
        
        completed_todos = [t for t in todo_list if t.get("completed", False)]
        remaining_todos = [t for t in todo_list if not t.get("completed", False)]
        
        context = f"Goal: {goal}\n\n"
        context += f"Current working directory: {current_observation.get('working_directory', '')}\n"
        context += f"Files: {', '.join(current_observation.get('files', [])[:15])}\n"
        context += f"Directories: {', '.join(current_observation.get('directories', [])[:10])}\n"
        context += f"\nTodo List Progress:\n"
        context += f"- Completed: {len(completed_todos)}/{len(todo_list)}\n"
        context += f"- Remaining: {[t.get('task') for t in remaining_todos]}\n"
        
        if action_history:
            context += f"\nRecent actions ({len(action_history)} total):\n"
            for i, action_item in enumerate(action_history[-3:], 1):
                action = action_item.get("action", {})
                result = action_item.get("result", {})
                context += f"{i}. {action.get('command', '')} -> "
                context += f"Success: {result.get('success', False)}\n"
                if result.get("stdout"):
                    context += f"   Output: {result.get('stdout', '')[:150]}\n"
        
        prompt = f"""You are a ReAct reasoning agent. Analyze the current state and determine:

1. Is the goal achieved? (goal_achieved: true/false)
2. Is the goal impossible to achieve? (goal_impossible: true/false)
3. What is the current state relative to the goal?
4. Should the todo list be updated? (update_todo_list: true/false)
5. What needs to be done next?

{context}

Return as JSON:
{{
  "goal_achieved": false,
  "goal_impossible": false,
  "update_todo_list": false,
  "analysis": "Your detailed analysis of the current state and what needs to be done",
  "progress": "What progress has been made toward the goal",
  "next_steps": "What should be done next to get closer to the goal"
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a ReAct reasoning agent. Analyze situations and determine if goals are achieved."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return self._parse_json_response(content)
            
        except Exception as e:
            return {
                "goal_achieved": False,
                "goal_impossible": False,
                "update_todo_list": False,
                "analysis": f"Reasoning error: {str(e)}",
                "error": str(e)
            }

    def _plan(
        self, 
        reasoning: Dict[str, Any],
        current_observation: Dict[str, Any],
        todo_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Plan the next action(s) based on reasoning and todo list"""
        
        goal = self.goal
        analysis = reasoning.get("analysis", "")
        next_steps = reasoning.get("next_steps", "")
        
        remaining_todos = [t for t in todo_list if not t.get("completed", False)]
        next_todo = remaining_todos[0] if remaining_todos else None
        
        prompt = f"""You are a ReAct planning agent. Plan the next action(s) based on reasoning and todo list.

Goal: {goal}

Reasoning Analysis:
{analysis}

Next Steps Suggested:
{next_steps}

Current Todo List:
{json.dumps([t.get('task') for t in remaining_todos[:5]], indent=2)}

Next Todo Item:
{json.dumps(next_todo, indent=2) if next_todo else 'None'}

Current State:
- Working directory: {current_observation.get('working_directory', '')}
- Files: {', '.join(current_observation.get('files', [])[:15])}

Plan 1-2 specific bash commands to work on the next todo item. Be specific and actionable.

Return as JSON:
{{
  "current_action_description": "What I'm doing now (e.g., 'Creating README.md file')",
  "next_action_description": "What I'll do next (e.g., 'Then I'll create requirements.txt')",
  "actions": [
    {{
      "command": "bash command to execute",
      "description": "What this command does",
      "expected_outcome": "What should happen if this succeeds",
      "todo_id": {next_todo.get('id') if next_todo else None}
    }}
  ],
  "no_action_needed": false
}}"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a ReAct planning agent. Plan safe, specific bash commands to achieve goals."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            content = response.choices[0].message.content
            return self._parse_json_response(content)
            
        except Exception as e:
            return {
                "current_action_description": f"Planning error: {str(e)}",
                "actions": [],
                "error": str(e)
            }

    def _act(
        self, 
        action: Dict[str, Any],
        auto_confirm: bool,
        verbose: bool
    ) -> Dict[str, Any]:
        """Execute an action (command)"""
        
        command = action.get("command", "")
        description = action.get("description", "")
        
        if not command:
            return {
                "success": False,
                "error": "No command provided",
                "critical_failure": False
            }
        
        if verbose:
            self.console.print(f"  [cyan]→ {command}[/cyan]")
            if description:
                self.console.print(f"    [dim]{description}[/dim]")
        
        # Safety check
        safety_result = self.safety_checker.check_commands([command])
        
        if safety_result.get("has_risky"):
            if verbose:
                self.display.show_risky_commands(safety_result["risky_commands"])
            
            has_critical = any(
                c.get("risk_level") == "CRITICAL" 
                for c in safety_result.get("risky_commands", [])
            )
            
            if not auto_confirm:
                if not self.display.confirm_risky_execution(
                    len(safety_result["risky_commands"]),
                    1,
                    has_critical
                ):
                    return {
                        "success": False,
                        "skipped": True,
                        "reason": "User cancelled risky action",
                        "critical_failure": False
                    }
        
        # Execute command
        execution_result = self.executor.execute_commands([command], [description])
        result = execution_result["results"][0] if execution_result["results"] else {}
        
        if verbose:
            if result.get("success"):
                self.console.print(f"    [green]✓ Success[/green]")
                if result.get("stdout"):
                    output = result.get("stdout", "").strip()
                    if output and len(output) < 200:
                        self.console.print(f"      [dim]{output}[/dim]")
            else:
                self.console.print(f"    [red]✗ Failed[/red]")
                if result.get("stderr"):
                    self.console.print(f"      [dim]Error: {result.get('stderr', '')[:200]}[/dim]")
        
        return {
            "success": result.get("success", False),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", -1),
            "critical_failure": not result.get("success", False) and result.get("exit_code", 0) != 0
        }

    def _mark_todo_completed(self, actions: List[Dict[str, Any]], action_results: List[Dict[str, Any]]):
        """Mark todos as completed based on successful actions"""
        for action, result in zip(actions, action_results):
            if result.get("success") and action.get("todo_id"):
                todo_id = action.get("todo_id")
                for todo in self.todo_list:
                    if todo.get("id") == todo_id:
                        todo["completed"] = True
                        break

    def _display_observation(self, observation: Dict[str, Any]):
        """Display an observation in a readable format"""
        files = observation.get("files", [])
        dirs = observation.get("directories", [])
        completed = observation.get("completed_todos", 0)
        total = observation.get("total_todos", 0)
        
        if files or dirs:
            items = []
            items.extend([f"[green]{f}[/green]" for f in files[:10]])
            items.extend([f"[blue]{d}/[/blue]" for d in dirs[:5]])
            if len(files) > 10 or len(dirs) > 5:
                items.append("[dim]...[/dim]")
            self.console.print(f"  Files/Dirs: {', '.join(items)}")
        
        if total > 0:
            self.console.print(f"  Todo Progress: {completed}/{total} completed")

    def _display_todo_list(self):
        """Display the current todo list"""
        if not self.todo_list:
            return
        
        table = Table(title="Todo List", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Task", style="white")
        table.add_column("Status", style="yellow", width=10)
        table.add_column("Priority", style="magenta", width=8)
        
        for todo in self.todo_list:
            todo_id = str(todo.get("id", "?"))
            task = todo.get("task", "")
            status = "[green]✓ Done[/green]" if todo.get("completed") else "[yellow]⏳ Todo[/yellow]"
            priority = todo.get("priority", "medium")
            
            table.add_row(todo_id, task, status, priority)
        
        self.console.print(table)

    def _generate_natural_language_summary(
        self,
        goal: str,
        goal_achieved: bool,
        final_reasoning: str,
        todo_list: List[Dict[str, Any]],
        action_history: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language summary like conversational mode"""
        
        completed_todos = [t for t in todo_list if t.get("completed", False)]
        total_actions = len(action_history)
        successful_actions = sum(1 for a in action_history if a.get("result", {}).get("success", False))
        
        context = f"""Goal: {goal}
Status: {"Achieved" if goal_achieved else "Not fully achieved"}
Final Reasoning: {final_reasoning}
Completed Todos: {len(completed_todos)}/{len(todo_list)}
Total Actions: {total_actions}
Successful Actions: {successful_actions}

Actions Taken:
"""
        for i, action_item in enumerate(action_history, 1):
            action = action_item.get("action", {})
            result = action_item.get("result", {})
            context += f"{i}. {action.get('command', '')} - "
            context += f"{'Success' if result.get('success') else 'Failed'}\n"
        
        prompt = f"""Generate a natural, conversational summary of the goal achievement process.

{context}

Provide a friendly, natural language response that:
- Summarizes what was accomplished
- Explains the process in a conversational way
- Mentions key steps taken
- Provides a clear conclusion

Write as if you're explaining to a friend what happened."""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Provide clear, friendly, conversational summaries."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I worked on achieving the goal '{goal}'. {'The goal was achieved!' if goal_achieved else 'The goal was not fully achieved.'} I executed {total_actions} actions, with {successful_actions} being successful."

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            content = content.strip()
            
            # Extract JSON from markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response",
                "goal_achieved": False,
                "goal_impossible": False,
                "analysis": content[:200]
            }
        except Exception as e:
            return {
                "error": str(e),
                "goal_achieved": False,
                "goal_impossible": False
            }

    def show_summary(self, result: Dict[str, Any]):
        """Display goal achievement summary with natural language response"""
        status = result.get("status", "unknown")
        status_icon = {
            "achieved": "✅",
            "impossible": "❌",
            "max_iterations": "⚠️",
            "interrupted": "⏸️"
        }.get(status, "❓")
        
        status_color = {
            "achieved": "green",
            "impossible": "red",
            "max_iterations": "yellow",
            "interrupted": "yellow"
        }.get(status, "white")
        
        summary_panel = Panel(
            f"[bold]{status_icon} Goal Achievement Summary[/bold]\n\n"
            f"Goal: {result.get('goal', 'Unknown')}\n"
            f"Status: {status}\n"
            f"Iterations: {result.get('iterations', 0)}\n"
            f"Total Actions: {result.get('total_actions', 0)}",
            title="ReAct Agent Summary",
            border_style=status_color
        )
        self.console.print(summary_panel)
        
        # Show natural language summary
        natural_summary = result.get("natural_language_summary", "")
        if natural_summary:
            self.console.print(f"\n[bold]💬 Summary:[/bold]")
            panel = Panel(
                Markdown(natural_summary),
                title="[bold green]✅ Result[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(panel)
        
        # Show todo list status
        todo_list = result.get("todo_list", [])
        if todo_list:
            completed = sum(1 for t in todo_list if t.get("completed", False))
            self.console.print(f"\n[dim]Todo List: {completed}/{len(todo_list)} completed[/dim]")
        
        # Show action history
        action_history = result.get("action_history", [])
        if action_history:
            table = Table(title="Action History", show_header=True)
            table.add_column("Iteration", style="cyan", width=8)
            table.add_column("Command", style="green")
            table.add_column("Result", style="yellow", width=10)
            
            for action_item in action_history:
                iteration = action_item.get("iteration", "?")
                action = action_item.get("action", {})
                result_item = action_item.get("result", {})
                command = action.get("command", "")[:50]
                success = "✅" if result_item.get("success") else "❌"
                
                table.add_row(str(iteration), command, success)
            
            self.console.print(table)
