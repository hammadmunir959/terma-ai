# 🤖 Terma AI - Natural Language Terminal Agent

**Goal-Oriented AI Agent for Linux Terminal**

Terma AI is an intelligent command-line tool that transforms your Linux terminal into a goal-oriented AI assistant. Instead of remembering commands, describe what you want to achieve in plain English. Powered by OpenRouter's free LLMs, it understands your goals, asks clarifying questions, plans the steps, and executes them safely with your confirmation.

![Version](https://img.shields.io/badge/version-1.4.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### V1 Core Features
- 🧠 **Natural Language Processing**: Convert plain English to bash commands
- 🛡️ **Smart Safety System**: Multi-layer safety checks with risk level classification
- ⚠️ **Risky Operation Warnings**: Dangerous commands flagged with prominent warnings
- ✅ **User Confirmation**: All commands require explicit approval (double confirmation for critical operations)
- 🎨 **Rich Terminal UI**: Beautiful, colored output with detailed feedback
- 🔧 **Configurable**: Support for multiple free OpenRouter models
- 📊 **Execution Tracking**: Detailed logs and execution summaries
- 🚀 **Fast & Lightweight**: Minimal dependencies, quick responses
- 🔓 **Flexible Control**: Execute risky operations after explicit confirmation

### 🆕 V2 Advanced Features
- 🐚 **Interactive Shell Mode**: Persistent terminal session with context retention
- 📋 **Multi-Step Task Planner**: Break complex tasks into ordered, executable steps
- ⚙️ **Preferences System**: Customize AI behavior (package manager, editor, verbosity, etc.)
- 🎯 **Risk Scoring (1-5)**: Detailed risk analysis with impact assessment
- 🔍 **Dry-Run Mode**: Preview commands without execution
- 📚 **Teaching Mode**: Learn Linux with detailed command explanations
- 💡 **Command Explanations**: Understand why commands are chosen and what they do
- 🛡️ **Safer Alternatives**: Get suggestions for safer command options
- 🔧 **Auto-Fix Errors**: Automatically analyze and fix failed commands
- 🔍 **Troubleshooting Agent**: Interactive system diagnosis and guided fixes
- 🚀 **Setup Wizard**: AI-guided environment setup for development stacks
- 📦 **Git Assistant**: Natural language Git commands
- 🌐 **Network Diagnostic AI**: Network checks with AI explanations
- 🎯 **Goal-Oriented Agent**: Understand, plan, and execute complex goals with clarification
- 💬 **Chat Mode**: Conversational AI assistant that answers questions and executes commands
- 🤖 **ReAct Agent**: Fully agentic goal achievement using Observe-Reason-Plan-Act methodology

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Linux terminal environment
- OpenRouter API key (free tier supported)

### Installation

#### Option 1: Install from PyPI (Recommended)

```bash
pip install terma-ai
```

After installation, you can use either `termai` or `terma` command (both work):

```bash
# Both commands work the same way
termai run "list files"
terma run "list files"

termai shell
terma shell

termai goal "backup my files"
terma goal "backup my files"
```

#### Option 2: Install from Source

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd terminal_ai
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or install in development mode:
   ```bash
   pip install -e .
   ```

4. **Configure API access**

   **Option A: Interactive Setup (Recommended)**
   ```bash
   terma setup-api
   # or
   termai setup-api
   ```
   This will guide you through setting up your OpenRouter API key interactively.

   **Option B: Manual Setup**
   ```bash
   # Create .env file with your OpenRouter API key
   echo "API_KEY=sk-or-v1-your-api-key-here" > .env
   ```

   **Option C: Environment Variable**
   ```bash
   export API_KEY=sk-or-v1-your-api-key-here
   # Or for permanent setup:
   echo 'export API_KEY=sk-or-v1-your-api-key-here' >> ~/.bashrc
   source ~/.bashrc
   ```

   **Get Your API Key:**
   - Visit: https://openrouter.ai/keys
   - Sign up for a free account (no credit card required)
   - Create a new API key
   - Copy the key (starts with `sk-or-v1-`)

5. **Test the installation**
   ```bash
   termai test
   # or
   terma test
   ```

   **Verify Configuration:**
   ```bash
   termai config
   # or
   terma config
   ```

## 📖 Usage Guide

### Getting Started

Once installed, you can use Terma AI directly from the command line. Both `termai` and `terma` commands work (use whichever you prefer):

```bash
# View all available commands
termai --help
# or
terma --help

# Check your configuration
termai config
# or
terma config

# Test API connectivity
termai test
# or
terma test
```

### Core Commands

#### 1. Basic Command Execution (`run`)

Execute natural language commands with safety checks:

```bash
# Simple file operations
termai run "list all files in current directory"
termai run "show disk usage"
termai run "find large files over 100MB"
termai run "count lines in all Python files"

# With options
termai run "list files" --cwd /home/user          # Specify working directory
termai run "show processes" --no-confirm         # Skip confirmation (use carefully!)
termai run "delete old logs" --dry-run           # Preview without executing
termai run "backup files" --verbose              # Show detailed output
```

**Options:**
- `--confirm` / `--no-confirm`: Control confirmation prompts (default: confirm)
- `--dry-run`: Preview commands without execution
- `--verbose` / `-v`: Show detailed output
- `--cwd <path>`: Set working directory for command execution

#### 2. Interactive Shell Mode (`shell`)

Start a persistent terminal session for continuous AI interaction:

```bash
# Start interactive shell
termai shell

# In the shell, you can run commands directly:
TermaShell > list files in current directory
TermaShell > create a new project folder
TermaShell > show disk usage
TermaShell > exit                    # Exit the shell
TermaShell > clear                   # Clear screen
TermaShell > help                    # Show help
TermaShell > cd /path/to/directory   # Change directory
```

**Benefits:**
- Maintains context across commands
- Faster workflow (no need to restart)
- Built-in commands: `exit`, `clear`, `help`, `history`, `cd <path>`

#### 3. Goal-Oriented Agent (`goal`) - V3

Execute complex, multi-step goals with automatic planning:

```bash
# Simple goals
termai goal "backup all my project files and compress them"
termai goal "setup a Node.js project with Express and TypeScript"
termai goal "clean old log files and free up disk space"

# With options
termai goal "deploy application" --dry-run    # Preview plan
termai goal "setup environment" --auto        # Auto-confirm all steps
```

**How it works:**
1. Understands your goal and asks clarifying questions if needed
2. Breaks down the goal into ordered steps
3. Executes steps safely with monitoring
4. Provides completion summary with insights

#### 3.5. Chat Mode (`chat`)

Conversational AI assistant that answers questions and executes commands when needed:

```bash
# Ask questions
termai chat "what is git?"
termai chat "explain how ls command works"
termai chat "how do I check disk usage?"

# Request actions
termai chat "list files in current directory"
termai chat "show me the contents of README.md"
termai chat "check git status"

# With options
termai chat "backup files" --cwd /home/user/projects
termai chat "install package" --no-auto-execute
```

**How it works:**
- Analyzes your query to determine if it needs command execution
- Answers questions conversationally (like ChatGPT)
- Executes commands when needed and provides natural language summaries
- Automatically handles safe commands, asks for confirmation on risky ones

#### 3.6. ReAct Agent (`react`)

Fully agentic goal achievement using Observe-Reason-Plan-Act methodology:

```bash
# Use ReAct agent for complex goals
termai react "set up a Python project with FastAPI and PostgreSQL"
termai react "create a backup system for my documents" --max-iterations 5
termai react "debug why my application is failing" --verbose

# With options
termai react "deploy application" --auto              # Auto-confirm actions
termai react "setup environment" --max-iterations 10 # More iterations
termai react "analyze system" --quiet               # Less verbose output
```

**How it works:**
1. **OBSERVE**: Checks current system state (files, directories, recent outputs)
2. **REASON**: Analyzes observations and determines next actions
3. **PLAN**: Creates a plan based on reasoning
4. **ACT**: Executes planned actions and observes results
5. **ITERATE**: Repeats until goal is achieved or max iterations reached

**Benefits:**
- Fully autonomous goal achievement
- Self-correcting through observation loops
- Handles complex, multi-step goals automatically
- Adapts to unexpected situations

### Advanced Features

#### 4. Multi-Step Task Planner (`plan`)

Plan and execute complex tasks step-by-step:

```bash
# Plan a task
termai plan "set up a Node.js project with Express"
termai plan "backup and compress files" --dry-run
termai plan "configure development environment" --cwd /path/to/project
```

**Example Output:**
```
📋 Task Plan: Set up a Node.js project with Express
Total steps: 4

Step 1: Create project directory
Command: mkdir my-project

Step 2: Initialize npm
Command: cd my-project && npm init -y

Step 3: Install Express
Command: npm install express

Step 4: Create app.js template
Command: echo 'const express = require("express");...' > app.js
```

#### 5. Preferences Management (`pref`)

Customize AI behavior and settings:

```bash
# List all preferences
termai pref list

# Set preferences
termai pref set package_manager pacman
termai pref set editor vim
termai pref set teaching_mode true
termai pref set verbosity high
termai pref set safety_mode strict

# Get a preference value
termai pref get package_manager

# Reset to defaults
termai pref reset
```

**Available Preferences:**
- `package_manager`: apt, yum, dnf, pacman
- `editor`: nano, vim, code, etc.
- `safety_mode`: confirm, strict, permissive
- `verbosity`: low, normal, high
- `teaching_mode`: true/false
- `default_confirm`: true/false
- `preferred_shell`: bash, zsh, fish

Preferences are saved to `~/.termai/preferences.yaml` and automatically applied.

#### 6. Command Explanations (`explain`)

Learn what commands do and why they're used:

```bash
# Basic explanation
termai explain "ls -la"

# Explain why a command was chosen
termai explain "sudo apt update" --why "update system packages"

# Get safer alternatives
termai explain "chmod 777 file" --safer

# Break down complex commands
termai explain "find . -name '*.py' -exec grep -l 'import' {} \\;" --breakdown
```

#### 7. Auto-Fix Errors (`fix`)

Automatically analyze and fix command errors:

```bash
# Analyze an error
termai fix "npm install" --stderr "npm: command not found"

# Auto-execute the fix
termai fix "python script.py" --stderr "ModuleNotFoundError" --auto

# Get detailed explanations
termai fix "docker run image" --stderr "permission denied" --teaching
```

**Options:**
- `--stderr <error>`: Error output from failed command
- `--stdout <output>`: Standard output (optional)
- `--return-code <code>`: Return code (default: 1)
- `--auto`: Automatically execute the suggested fix
- `--teaching`: Show detailed explanations

#### 8. Troubleshooting Agent (`troubleshoot`)

Interactive system diagnosis and guided fixes:

```bash
# Start troubleshooting session
termai troubleshoot

# Start with initial symptom
termai troubleshoot "system is slow"
termai troubleshoot "network connection issues"
termai troubleshoot "application crashes"
```

The agent will:
1. Ask targeted questions to narrow down the issue
2. Analyze symptoms and system information
3. Provide probable root cause with confidence level
4. Offer step-by-step guided fixes

#### 9. Environment Setup Wizard (`setup`)

AI-guided setup for complete development environments:

```bash
# List available templates
termai setup-list

# Set up an environment
termai setup django
termai setup nodejs --version 18
termai setup python --name myproject
termai setup django --database postgresql --features "redis,cache"
```

**Available Templates:**
- `django`, `flask` - Web frameworks
- `nodejs`, `react`, `vue` - JavaScript environments
- `python`, `rust`, `go`, `java`, `php`, `ruby` - Language environments
- `full-stack` - Complete development setup

#### 10. Git Assistant (`git`)

Natural language Git commands:

```bash
# Convert natural language to Git commands
termai git run "undo last commit but keep changes"
termai git run "create a new branch called feature" --execute
termai git run "show recent commits" --explain
termai git run "stage all files and commit with message"
termai git run "merge feature branch into main"
```

**Options:**
- `--execute` / `-e`: Execute the generated commands
- `--explain`: Show detailed explanations

#### 11. Network Diagnostic (`network`)

Network checks with AI explanations:

```bash
# Ping a host
termai network ping google.com
termai network ping 8.8.8.8 --count 10

# Trace route
termai network trace github.com

# Check port
termai network port google.com 80
termai network port localhost 3306

# DNS lookup
termai network dns github.com
termai network dns api.example.com
```

**Options:**
- `--explain` / `--no-explain`: Show/hide AI explanations (default: explain)
- `--count <n>`: Number of ping packets (ping only)

### Utility Commands

#### API Key Setup (`setup-api`)

Interactive setup for OpenRouter API key:

```bash
termai setup-api
# or
terma setup-api
```

This command will:
1. Guide you through entering your API key
2. Save it to a `.env` file in your current directory
3. Verify the setup

**Get Your API Key:**
- Visit: https://openrouter.ai/keys
- Sign up for a free account (no credit card required)
- Create a new API key
- Your key will look like: `sk-or-v1-xxxxxxxxxxxxxxxxxxxxx`

**Note:** If you try to use any AI-powered command without an API key, Terma AI will automatically show you instructions on how to set it up.

#### Configuration (`config`)

View current configuration:

```bash
termai config
# or
terma config
```

Shows:
- Provider (OpenRouter)
- Model name
- Temperature
- Max tokens
- API base URL
- API key status (masked for security)

If API key is missing, it will suggest running `terma setup-api`.

#### Testing (`test`)

Test components and API connectivity:

```bash
termai test
termai test --verbose
```

Tests:
- LLM API connection
- Safety checker functionality
- Command executor

### Command Options Reference

**Global Options:**
- `--help`: Show help message
- `--verbose` / `-v`: Show detailed output

**Safety Options:**
- `--confirm` (default): Require confirmation for all commands
- `--no-confirm`: Skip confirmation (use with caution!)
- `--dry-run`: Preview commands without execution

**Note:** Even with `--no-confirm`, risky commands are still flagged with warnings. Always review commands carefully, especially for system administration tasks.

### Quick Reference

```bash
# Most common commands (both 'termai' and 'terma' work)
termai run "your natural language request"      # or: terma run "..."
termai shell                                    # Interactive mode
termai goal "complex multi-step goal"           # Goal-oriented agent

# Learning and help
termai explain "command"                       # Learn commands
termai pref list                               # View preferences
termai config                                  # Check configuration

# Advanced features
termai plan "multi-step task"                  # Task planning
termai fix "command" --stderr "error"         # Error fixing
termai troubleshoot "symptom"                 # System diagnosis
termai setup <environment>                     # Environment setup
termai git run "git request"                   # Git operations
termai network ping <host>                    # Network diagnostics
termai chat "your question"                    # Conversational AI
termai react "complex goal"                    # ReAct agent

# Note: You can use 'terma' instead of 'termai' for all commands
# Example: terma run "list files" works the same as termai run "list files"
```

### Command Examples

Terma AI can handle various types of requests:

```bash
# File operations (Safe)
termai run "create a backup of my documents folder"
termai run "find all PDF files modified in the last week"
termai run "compress the downloads folder"

# System monitoring (Safe)
termai run "show running processes"
termai run "check memory usage"
termai run "display disk space information"

# Network operations (Safe)
termai run "test internet connectivity"
termai run "show network interfaces"

# Development tasks (Safe)
termai run "initialize a git repository"
termai run "show git status"
termai run "find all Python files with syntax errors"

# Risky operations (Requires confirmation)
termai run "update system packages with sudo"
termai run "change file permissions to 777 recursively"
termai run "install a package using apt"
```

### Handling Risky Commands

When you request a risky operation, Terma AI will:

1. **Flag the command** with a prominent warning panel
2. **Show the risk level** (CRITICAL, HIGH, or MEDIUM)
3. **Display the reason** why it's risky
4. **Request confirmation** before execution

**Example:**
```bash
$ termai run "run sudo apt update"

⚠️  HIGH RISK COMMANDS DETECTED ⚠️
These commands modify system files or require elevated privileges!

╭─────────────────── ⚠️  HIGH RISK - Command 1 ────────────────────╮
│ sudo apt update                                                   │
│                                                                   │
│ Blocked: sudo commands require manual execution                  │
╰───────────────────────────────────────────────────────────────────╯

⚠️  RISKY OPERATION WARNING ⚠️
Do you want to proceed with 1 risky command(s)? [y/n] (n):
```

**For critical commands:**
```bash
$ termai run "delete everything in root directory"

🚨 CRITICAL RISK WARNING 🚨
You are about to execute commands that can DESTROY your system!
Are you ABSOLUTELY SURE you want to proceed? [y/n] (n): y
FINAL WARNING: This may destroy your system. Type 'yes' again to proceed [y/n] (n): y
```

## 🆕 V2 Features

### 🐚 Feature 1: Interactive Shell Mode

Start a persistent terminal session where you can continuously interact with the AI:

```bash
# Start interactive shell
termai shell

# In the shell:
TermaShell > list files in current directory
TermaShell > create a new project folder
TermaShell > show disk usage
TermaShell > exit
```

**Benefits:**
- Maintains context across commands
- Faster workflow (no need to restart)
- Built-in commands: `exit`, `clear`, `help`, `history`, `cd <path>`
- Preferences automatically applied

### 📋 Feature 2: Multi-Step Task Planner

Break down complex tasks into ordered steps and execute them safely:

```bash
# Plan and execute a multi-step task
termai plan "set up a Node.js project with Express"

# Preview plan without executing
termai plan "create backup and compress files" --dry-run
```

**Example Output:**
```
📋 Task Plan: Set up a Node.js project with Express
Total steps: 4

Step 1: Create project directory
Command: mkdir my-project

Step 2: Initialize npm
Command: cd my-project && npm init -y

Step 3: Install Express
Command: npm install express

Step 4: Create app.js template
Command: echo 'const express = require("express");...' > app.js
```

### ⚙️ Feature 3: Preferences System

Customize how Terma AI behaves:

```bash
# List all preferences
termai pref list

# Set preferences
termai pref set package_manager pacman
termai pref set editor vim
termai pref set teaching_mode true
termai pref set verbosity high

# Get a preference
termai pref get package_manager

# Reset to defaults
termai pref reset
```

**Available Preferences:**
- `package_manager`: apt, yum, dnf, pacman
- `editor`: nano, vim, code, etc.
- `safety_mode`: confirm, strict, permissive
- `verbosity`: low, normal, high
- `teaching_mode`: true/false
- `default_confirm`: true/false
- `preferred_shell`: bash, zsh, fish

Preferences are saved to `~/.termai/preferences.yaml` and automatically applied to all AI interactions.

### 🎯 Feature 4: Enhanced Safety Engine

**Risk Scoring (1-5):**
- **Level 1**: Harmless read operations (`ls`, `cat`, `find`)
- **Level 2**: Potentially risky (`rm -rf`, `chmod -R`)
- **Level 3**: System modification with sudo (`sudo apt`, `iptables`)
- **Level 4**: Critical system modification (`> /etc/`, `chmod 777 -R /`)
- **Level 5**: System destruction (`rm -rf /`, `dd if=/dev/zero`, `mkfs`)

**Dry-Run Mode:**
Preview commands without executing them:

```bash
# See what would be executed
termai run "delete old log files" --dry-run

# In task planner
termai plan "set up web server" --dry-run
```

**Impact Analysis:**
Each risky command shows:
- Risk score and level
- Potential effects
- Safer alternatives

### 📚 Feature 5: Teaching Mode & Explanations

Learn Linux commands with detailed explanations:

```bash
# Explain what a command does
termai explain "ls -la"

# Explain why a command was chosen
termai explain "sudo apt update" --why "update system packages"

# Get safer alternatives
termai explain "chmod 777 file" --safer

# Break down complex commands
termai explain "find . -name '*.py' -exec grep -l 'import' {} \\;" --breakdown
```

**Example Explanation:**
```
📖 Explanation: ls -la

What the command does:
The `ls -la` command lists all files and folders in your current directory,
including hidden files, with detailed information like size, owner, and permissions.

What each part means:
- `ls`: List command
- `-l`: Long format (detailed view)
- `-a`: All files (including hidden)

⚠️ Risk Analysis:
  Risk Score: 1/5 (LOW)
```

**Teaching Mode:**
Enable in preferences to get detailed explanations for all commands:
```bash
termai pref set teaching_mode true
```

### 🔧 Feature 4: Auto-Fix Terminal Errors

Automatically analyze and fix command errors:

```bash
# Analyze an error and get fixes
termai fix "npm install" --stderr "npm: command not found"

# Auto-execute the suggested fix
termai fix "python script.py" --stderr "ModuleNotFoundError" --auto

# Get detailed explanations
termai fix "docker run image" --stderr "permission denied" --teaching
```

**How it works:**
1. Analyzes the error output and return code
2. Identifies the root cause
3. Suggests 1-3 fix options with confidence levels
4. Optionally auto-executes the fix
5. Explains how to prevent the error in the future

**Example:**
```
❌ Command Failed: npm install
Error: npm command not found

🔧 Suggested Fixes:

🟢 Fix 1: sudo apt update && sudo apt install -y nodejs npm
   Installs Node.js and npm via APT package manager

🟢 Fix 2: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
   Installs from NodeSource repository for latest LTS version

💡 Prevention: Verify installation with 'npm --version' before running commands
```

### 🔍 Feature 5: System Troubleshooting Agent

Interactive diagnostic assistant that asks questions to identify system issues:

```bash
# Start troubleshooting session
termai troubleshoot

# Start with initial symptom
termai troubleshoot "system is slow"
termai troubleshoot "network connection issues"
termai troubleshoot "application crashes"
```

**How it works:**
1. Asks targeted questions to narrow down the issue
2. Analyzes symptoms and system information
3. Provides probable root cause with confidence level
4. Offers step-by-step guided fixes
5. Optionally executes fixes with your approval

**Example Session:**
```
🔍 System Troubleshooting Agent

Initial Symptom: system is slow

❓ Can you describe when the slowness occurs?
Your answer: When opening applications

❓ Which applications are slowest?
Your answer: Firefox and VS Code

✅ Diagnosis Complete

🔍 Probable Root Cause:
🟢 High memory usage from multiple applications

🔧 Recommended Fixes:
Step 1: Check memory usage
  Command: free -h
  Explanation: Identify current memory consumption

Step 2: Kill memory-intensive processes
  Command: pkill -f firefox
  Explanation: Free up memory by closing heavy applications
```

### 🚀 Feature 6: Environment Setup Wizard

AI-guided setup for complete development environments:

```bash
# List available templates
termai setup-list

# Set up an environment
termai setup django
termai setup nodejs --version 18
termai setup python --name myproject
termai setup django --database postgresql --features "redis,cache"
```

**Available Templates:**
- `django` - Django web framework
- `flask` - Flask web framework
- `nodejs` - Node.js environment
- `react` - React application
- `vue` - Vue.js application
- `python` - Python development environment
- `rust` - Rust development environment
- `go` - Go development environment
- `java` - Java development environment
- `php` - PHP development environment
- `ruby` - Ruby development environment
- `full-stack` - Full-stack development setup

**How it works:**
1. Generates a complete setup plan with ordered steps
2. Shows all commands before execution
3. Handles dependencies, virtual environments, and configuration
4. Executes steps sequentially with safety checks
5. Provides progress updates and error handling

**Example:**
```
🚀 Environment Setup Wizard
Setting up: django

📋 Setup Plan: Set up Django environment with PostgreSQL
Total steps: 6

1. Create project directory
   mkdir myproject && cd myproject

2. Create virtual environment
   python3 -m venv .venv

3. Activate and upgrade pip
   .venv/bin/pip install --upgrade pip

4. Install Django
   .venv/bin/pip install django

5. Initialize Django project
   .venv/bin/django-admin startproject myproject .

6. Install PostgreSQL adapter
   .venv/bin/pip install psycopg2-binary

Proceed with setup? [y/n] (y):
```

### 📦 Feature 13: Git Assistant (Natural Language Git)

Simplify complex Git operations with natural language:

```bash
# Convert natural language to Git commands
termai git run "undo last commit but keep changes"
termai git run "create a new branch called feature" --execute
termai git run "show recent commits" --explain
termai git run "stage all files and commit with message"
termai git run "merge feature branch into main"
termai git run "push changes to remote repository"
```

**How it works:**
1. Converts natural language requests to Git commands
2. Provides clear explanations for each command
3. Warns about destructive operations (force push, hard reset)
4. Optionally executes commands with safety checks
5. Breaks complex operations into ordered steps

**Example:**
```
📋 Generated Commands
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command                    ┃ Explanation                                                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1. git reset --soft HEAD~1 │ Undoes the last commit while keeping all changes staged         │
└────────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

**Supported Operations:**
- Commits, staging, and status
- Branch creation and switching
- Merging and rebasing
- Push/pull operations
- Undo operations (reset, revert, restore)
- Stash operations
- Remote management
- Log and history viewing

### 🌐 Feature 14: Network Diagnostic AI

Run network checks and get AI-explained results:

```bash
# Ping a host with AI explanation
termai network ping google.com
termai network ping 8.8.8.8 --count 10

# Trace route with analysis
termai network trace github.com

# Check if a port is open
termai network port google.com 80
termai network port localhost 3306

# DNS lookup with explanation
termai network dns github.com
termai network dns api.example.com
```

**How it works:**
1. Runs standard network diagnostic commands
2. Parses and analyzes the results
3. Provides AI-powered explanations in simple terms
4. Identifies issues and suggests solutions
5. Explains what the numbers mean

**Example Ping Results:**
```
🌐 Pinging: google.com

📊 Results:
These ping results show a perfect connection to google.com. Your device sent 4 packets,
and all came back successfully with no delays or losses. The round-trip time averaged
about 42 milliseconds, which is fast and normal for internet browsing.

No issues detected:
- 0% packet loss (every packet made it)
- Low, consistent response times (39-43 ms)
- No lag, drops, or errors
```

**Example Port Check:**
```
🔌 Checking port: google.com:80

📊 Port Status:
Port 80 on google.com is OPEN. This means:
- The host is reachable and accepting connections
- Port 80 is typically used for HTTP web traffic
- This is expected for a web server like Google

If the port were closed, it might indicate:
- Firewall blocking the port
- Service not running
- Network connectivity issues
```

**Available Diagnostics:**
- **Ping**: Test connectivity and latency
- **Traceroute**: Map network path and identify bottlenecks
- **Port Check**: Verify if services are accessible
- **DNS Lookup**: Resolve hostnames and check DNS records

### 🎯 Feature 15: Goal-Oriented Agent (V3)

Transform Terma AI from a command executor to a **true goal-oriented agent** that understands, plans, and executes complex goals.

```bash
# Execute complex goals with automatic planning
termai goal "backup all my project files, compress them, and upload to Google Drive"
termai goal "setup a Node.js project with Express and TypeScript"
termai goal "clean old log files and free up disk space" --dry-run
termai goal "deploy my application to production" --auto
```

**How it works:**

1. **Goal Understanding & Clarification**
   - Analyzes your goal for ambiguities
   - Asks targeted questions if clarification is needed
   - Uses smart defaults for common scenarios
   - Filters obvious questions (e.g., OS type in Linux environment)

2. **Goal Decomposition**
   - Breaks complex goals into ordered, executable steps
   - Maps dependencies between steps
   - Identifies risky operations
   - Estimates completion time

3. **Dynamic Clarification Loop**
   - Interactive Q&A for ambiguous requests
   - Prevents wrong or destructive commands
   - Type 'skip' to use defaults
   - Type 'cancel' to abort

4. **Sequential Safe Execution**
   - Executes steps one at a time with monitoring
   - Checks success/failure after each step
   - Handles errors with retry/skip/abort options
   - Safety checks for risky operations
   - Progress tracking and time measurement

5. **Goal Completion Summary**
   - Summarizes execution with AI insights
   - Provides learning suggestions
   - Shows step-by-step results
   - Identifies improvements for next time

**Example Goal Execution:**
```
🎯 Goal-Oriented Agent
Goal: backup all my project files, compress them, and upload to Google Drive

❓ Goal Clarification Needed
Question 1: Which directory contains your project files?
Your answer: /home/user/projects

Question 2: What compression format? (zip, tar.gz, etc.)
Your answer: tar.gz

📋 Goal Plan: Backup, compress, and upload project files
Estimated time: 2-5 minutes

Execution Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━-by-step results
```

The replacement is too long. Let me use a shorter version:
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
read_file

Terma AI implements a smart safety system that **flags risky operations** instead of blocking them. All risky commands require **explicit user confirmation** before execution.

### 🚨 Risk Level Classification

Commands are classified into three risk levels:

#### **CRITICAL RISK** (Double Confirmation Required)
These commands can **destroy your system** or cause **irreversible damage**:
- `rm -rf /` - System destruction
- `dd if=/dev/zero` - Disk overwriting
- `mkfs` - Filesystem formatting
- `fdisk`, `parted` - Disk partitioning
- `kill -9 -1` - Killing all processes

**Confirmation Flow:**
1. First prompt: "Are you ABSOLUTELY SURE you want to proceed?"
2. Second prompt: "FINAL WARNING: This may destroy your system. Type 'yes' again to proceed"

#### **HIGH RISK** (Single Confirmation with Warning)
These commands modify system files or require elevated privileges:
- `sudo` commands - Privilege escalation
- `> /etc/passwd` - System file modification
- `> /boot/`, `> /bin/` - System directory modification
- `chmod 777 -R /` - Dangerous permissions
- `chown root` - Changing ownership to root
- `iptables -F` - Flushing firewall rules

**Confirmation Flow:**
- Single prompt with prominent warning panel

#### **MEDIUM RISK** (Standard Confirmation)
Other potentially risky operations that require attention.

### ⚠️ Warning Operations (Not Blocked)
These commands show warnings but are not blocked:
- Recursive operations (`chmod -R`, `chown -R`)
- Network downloads (`wget`, `curl`)
- Package management (`apt`, `yum`, `pacman`)
- Large directory searches (`find /`, `grep -r`)

### ✅ Safe Operations
These commands execute with standard confirmation:
- Read-only commands (`ls`, `cat`, `find`)
- Basic file operations in user directories
- System monitoring (`ps`, `df`, `free`)
- Text processing (`grep`, `sed`, `awk`)

### 🔒 Confirmation System

**Safe Commands:**
```
🔒 Ready to execute 1 safe command(s)? [y/n] (n):
```

**Risky Commands (HIGH/MEDIUM):**
```
⚠️  RISKY OPERATION WARNING ⚠️
You are about to execute commands that may modify system files...
Do you want to proceed with 1 risky command(s)? [y/n] (n):
```

**Critical Commands (CRITICAL):**
```
🚨 CRITICAL RISK WARNING 🚨
You are about to execute commands that can DESTROY your system!
Are you ABSOLUTELY SURE you want to proceed? [y/n] (n):
FINAL WARNING: This may destroy your system. Type 'yes' again to proceed [y/n] (n):
```

### 📋 Quick Reference: Risk Levels (V2 Enhanced)

| Risk Score | Risk Level | Examples | Confirmation Required |
|------------|------------|----------|----------------------|
| **5/5** | **CRITICAL** | `rm -rf /`, `dd if=/dev/zero`, `mkfs`, `fdisk` | Double confirmation |
| **4/5** | **HIGH** | `> /etc/passwd`, `chmod 777 -R /`, `> /boot/` | Single confirmation with warning |
| **3/5** | **MEDIUM-HIGH** | `sudo apt`, `iptables -F`, `chmod 777 -R` | Single confirmation with warning |
| **2/5** | **MEDIUM** | `rm -rf`, `chmod -R`, `chown -R` | Standard confirmation |
| **1/5** | **LOW** | `ls`, `cat`, `find`, `ps`, `df` | Standard confirmation |

**Risk Score Calculation:**
- Automatically calculated for all commands
- Visible in explanations and safety analysis
- Used for impact assessment and safer alternative suggestions

## ⚙️ Configuration

### Model Configuration

Edit `termai/settings.yaml` to configure different models:

```yaml
provider: "openrouter"
model: "x-ai/grok-4.1-fast:free"  # Your preferred model
temperature: 0.2
max_tokens: 300

# Fallback models (used if primary fails)
fallback_models:
  - "meta-llama/llama-3.3-70b-instruct:free"
  - "qwen/qwen-2.5-7b-instruct:free"
  - "google/gemma-2-9b-it:free"
```

### Supported Models

Terma AI works with OpenRouter's free models:
- **x-ai/grok-4.1-fast:free** (Recommended)
- **meta-llama/llama-3.3-70b-instruct:free**
- **qwen/qwen-2.5-7b-instruct:free**
- **google/gemma-2-9b-it:free**

## 🏗️ Architecture

```
┌──────────────┐
│   User CLI    │ ← Typer interface
└───────┬──────┘
        │
        ▼
┌────────────────────┐
│ Natural Language    │ ← OpenRouter API
│ Interpreter (LLM)   │
└───────┬────────────┘
        │ Commands + reasons
        ▼
┌────────────────────┐
│ Safety Checker      │ ← Pattern matching + Risk classification
│ (Flags risky ops)   │
└───────┬────────────┘
        │ Safe + Risky commands (flagged)
        ▼
┌────────────────────┐
│ Display Manager     │ ← Shows risk warnings
│ (Rich UI)          │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ User Confirmation   │ ← Interactive prompt
│ (Level-based)       │   - Standard for safe
└───────┬────────────┘   - Enhanced for risky
        │                 - Double for critical
        │ yes/no
        ▼
┌────────────────────┐
│ Command Executor    │ ← subprocess.run()
│ (Safe + Risky)     │
└────────────────────┘
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_safety.py -v
python -m pytest tests/test_llm.py -v
python -m pytest tests/test_executor.py -v

# Run with coverage
python -m pytest tests/ --cov=termai --cov-report=html
```

## 📋 Development Roadmap

### ✅ Phase 1: Core Infrastructure (Completed)
- [x] Python project setup with dependencies
- [x] OpenRouter API integration
- [x] Basic LLM interpreter
- [x] Safety checker with pattern matching
- [x] Command executor with subprocess
- [x] CLI interface with typer
- [x] User confirmation system
- [x] Rich terminal output

### ✅ Phase 2: V2 Advanced Features (Completed)
- [x] Interactive Shell Mode (Terma Shell)
- [x] Multi-Step Task Planner
- [x] Preferences System
- [x] Enhanced Safety Engine with Risk Scoring (1-5)
- [x] Dry-Run Mode
- [x] Teaching Mode & Command Explanations
- [x] Safer Alternatives Suggestions
- [x] Risk Impact Analysis
- [x] Auto-Fix Terminal Errors
- [x] System Troubleshooting Agent
- [x] Environment Setup Wizard
- [x] Git Assistant (Natural Language Git)
- [x] Network Diagnostic AI

### ✅ Phase 3: Goal-Oriented Agent (V3) (Completed)
- [x] Goal Understanding & Clarification System
- [x] Goal Decomposition with Dependencies
- [x] Dynamic Clarification Loop
- [x] Sequential Safe Execution with Monitoring
- [x] Goal Completion Summary & Learning
- [x] Error Handling with Retry/Skip/Abort
- [x] Progress Tracking and Time Measurement

### 🚧 Phase 4: Future Enhancements
- [ ] Advanced safety guardrail engine
- [ ] Error handling and logging improvements
- [ ] Performance optimization
- [ ] Docker containerization
- [ ] Plugin system
- [ ] Command history and replay

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `python -m pytest tests/`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Terma AI is designed with safety in mind, but use at your own risk.** 

The system implements multiple safety layers:
- ✅ **Risky commands are flagged** with prominent warnings
- ✅ **Risk levels are classified** (CRITICAL, HIGH, MEDIUM)
- ✅ **Explicit confirmation required** for all risky operations
- ✅ **Double confirmation** for critical operations

**However:**
- ⚠️ The system **allows risky operations** after your explicit confirmation
- ⚠️ **You are responsible** for reviewing and approving all commands
- ⚠️ **Critical operations** can destroy your system if confirmed
- ⚠️ Always review commands carefully, especially for system administration tasks
- ⚠️ The AI may generate commands that are not exactly what you intended

**Best Practices:**
- Review all generated commands before confirming
- Use `--verbose` flag to see detailed command explanations
- Test commands in a safe environment first
- Keep backups of important data
- Be extra cautious with CRITICAL risk commands

## 🙏 Acknowledgments

- **OpenRouter** for providing free LLM API access
- **xAI** for the Grok model
- **Rich** library for beautiful terminal output
- **Typer** for the CLI framework

---

**Made with ❤️ for the Linux community**
