"""
Bash Tool Handler for Claude's Bash Tool

This module provides a handler for Claude's bash tool, which enables executing
bash commands in a controlled environment. The bash tool is client-side,
meaning your application executes all commands locally.

Usage:
    from bash_tool import BashToolHandler

    handler = BashToolHandler()
    result = handler.handle(tool_input)
"""

import subprocess
from typing import Dict, Any


class BashToolHandler:
    """
    Handler for Claude's bash tool commands.

    The bash tool allows Claude to execute shell commands in a controlled environment.

    Security:
        This handler executes arbitrary commands which can be dangerous.
        In production environments, you should implement:
        - Command whitelisting
        - Sandboxing/containerization
        - User permissions restrictions
        - Resource limits (timeout, memory, etc.)
    """

    def __init__(self, timeout: int = 60, working_dir: str = None):
        """
        Initialize the bash tool handler.

        Args:
            timeout: Maximum execution time in seconds (default: 60)
            working_dir: Working directory for commands (default: current directory)
        """
        self.timeout = timeout
        self.working_dir = working_dir

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a bash tool command from Claude.

        Args:
            tool_input: Dictionary containing 'command' and optional 'restart' flag

        Returns:
            Dictionary with command output, error (if any), and exit code
        """
        command = tool_input.get("command", "")
        restart = tool_input.get("restart", False)

        if restart:
            # The restart flag indicates starting a fresh session
            # For this simple implementation, we just note it
            return {
                "message": "New bash session started",
                "output": ""
            }

        if not command:
            return {
                "error": "No command provided",
                "output": "",
                "exit_code": 1
            }

        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_dir
            )

            # Prepare response
            response = {
                "output": result.stdout,
                "exit_code": result.returncode
            }

            if result.stderr:
                response["error"] = result.stderr

            if result.returncode == 0:
                response["message"] = f"Command executed successfully"
            else:
                response["message"] = f"Command exited with code {result.returncode}"

            return response

        except subprocess.TimeoutExpired:
            return {
                "error": f"Command timed out after {self.timeout} seconds",
                "output": "",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "error": f"Error executing command: {str(e)}",
                "output": "",
                "exit_code": -1
            }


# Convenience function for backward compatibility
def handle_bash_tool(tool_input: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    """
    Convenience function to handle bash tool commands.

    This function creates a BashToolHandler instance and processes the command.
    For better performance when handling multiple commands, create a handler instance
    and reuse it.

    Args:
        tool_input: Dictionary containing 'command' and command-specific parameters
        timeout: Maximum execution time in seconds (default: 60)

    Returns:
        Dictionary with the result of the operation
    """
    handler = BashToolHandler(timeout=timeout)
    return handler.handle(tool_input)
