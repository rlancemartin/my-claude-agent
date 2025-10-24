# Open Claude Agent 

An open-source implementation of an agent harness, using Claude's recent tool capabilities and a few context engineering techniques that we've seen from popular agents such as [Manus](https://rlancemartin.github.io/2025/10/15/manus/): **reduction**, **isolation**, and **offloading**.

## Quickstart

```bash
# Install uv if you haven't already (https://docs.astral.sh/uv/)
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone or navigate to the project
cd open_claude_agent

# Sync dependencies (creates venv and installs everything from pyproject.toml)
uv sync

# Set your API key
export ANTHROPIC_API_KEY=your_key_here
```

## Overview

This project provides a simple, reusable agent harness that leverages Claude's native tool capabilities (memory, bash) combined with proven context engineering techniques. Rather than building a monolithic agent, this harness demonstrates how to efficiently manage context at scale using three key strategies:

- **Offloading**: Store information externally using Claude's memory tool and retrieve it on-demand rather than keeping everything in context
- **Reduction**: Use Claude's context management features to automatically trim older tool uses while preserving recent interactions
- **Isolation**: Execute bash commands in an isolated scratchpad directory to keep working files separate from source code

The harness is built around a reusable `ClaudeHarness` class that can be easily configured for different tool combinations, making it straightforward to extend with additional capabilities.

## Project Structure

```
open_claude_code/
├── README.md                      # This file
├── pyproject.toml                 # Project dependencies and configuration
└── src/open_claude_agent/         # Main package
    ├── __init__.py               # Package initialization
    ├── claude_harness.py         # Reusable harness for Claude API with tool support
    ├── memory_tool.py            # Memory tool handler (file operations in scratchpad)
    ├── bash_tool.py              # Bash tool handler (command execution in scratchpad)
    ├── utils.py                  # Formatting utilities for tool calls and results
    ├── test.ipynb                # Interactive demo notebook
    └── scratchpad/               # Isolated working directory for tools
        └── (files created by memory/bash tools)
```

## Tools & Capabilities

This harness supports Claude's native tool capabilities through modular handlers:

### Memory Tool
*Store and retrieve persistent information across conversations*

| Command | Description | Example Use Case |
|---------|-------------|------------------|
| `view` | List directory contents or read file contents | Check what files exist, read stored data |
| `create` | Create or overwrite a file | Save user preferences, store analysis results |
| `str_replace` | Replace text within a file | Update specific values in config files |
| `insert` | Insert text at a specific line | Add new entries to lists |
| `delete` | Delete a file or directory | Clean up temporary files |
| `rename` | Rename or move a file/directory | Reorganize stored information |

**Reference**: [Claude Memory Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool)

### Bash Tool
*Execute shell commands in the scratchpad directory*

| Feature | Description | Example Use Case |
|---------|-------------|------------------|
| Command execution | Run any bash command with timeout protection | Create files, process data, run scripts |
| Working directory | Commands execute in isolated scratchpad | Keep test files separate from source |
| Output capture | Captures stdout, stderr, and exit codes | Verify command success, read results |

**Reference**: [Claude Bash Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool)

### Claude Harness
*Reusable framework for tool integration*

The `ClaudeHarness` class provides a flexible foundation that handles:
- Tool execution loops and conversation management
- Automatic tool result formatting and display
- Support for multiple tools in a single session
- Configurable models, betas, and context management

**Extending**: Add new tools by creating a handler class with a `handle(tool_input)` method and registering it with the harness.
