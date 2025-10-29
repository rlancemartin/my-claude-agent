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
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


class BashSession:
    """
    Maintains a persistent bash session using subprocess.Popen.

    This allows environment variables and working directory changes to persist
    across multiple commands in the same session.
    """

    def __init__(self, working_dir: Optional[str] = None):
        """
        Initialize a new bash session.

        Args:
            working_dir: Working directory for the session
        """
        self.working_dir = working_dir
        self.process = None
        self._start_session()

    def _start_session(self):
        """Start a new bash process."""
        self.process = subprocess.Popen(
            ['/bin/bash'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.working_dir,
            bufsize=1
        )

    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command in the bash session.

        Args:
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            Dictionary with output, error, and exit code
        """
        try:
            # Send command to bash process
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()

            # Wait for command to complete with timeout
            stdout, stderr = self.process.communicate(timeout=timeout)

            return {
                "output": stdout,
                "error": stderr if stderr else None,
                "exit_code": self.process.returncode or 0
            }
        except subprocess.TimeoutExpired:
            self.process.kill()
            self._start_session()  # Restart session after timeout
            return {
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "exit_code": -1
            }

    def restart(self):
        """Restart the bash session."""
        if self.process:
            self.process.kill()
        self._start_session()

    def close(self):
        """Close the bash session."""
        if self.process:
            self.process.kill()


class BashToolHandler:
    """
    Handler for Claude's bash tool commands following best practices.

    The bash tool allows Claude to execute shell commands in a controlled environment
    with validation, timeout protection, output sanitization, and logging.

    Security:
        This handler executes arbitrary commands which can be dangerous.
        In production environments, you should implement:
        - Command whitelisting/validation
        - Sandboxing/containerization
        - User permissions restrictions
        - Resource limits (timeout, memory, etc.)
    """

    # Dangerous command patterns to block
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',  # Recursive delete from root
        r':\(\)\{\s*:\|:&\s*\};:',  # Fork bomb
        r'mkfs\.',  # Format filesystem
        r'dd\s+if=/dev/zero',  # Disk wipe patterns
        r'wget.*\|\s*sh',  # Download and execute
        r'curl.*\|\s*sh',  # Download and execute
    ]

    # Sensitive data patterns to sanitize
    SENSITIVE_PATTERNS = [
        (r'[A-Za-z0-9]{20,}', '[REDACTED_TOKEN]'),  # API tokens
        (r'password\s*=\s*["\']?[^"\'\s]+', 'password=[REDACTED]'),  # Passwords
        (r'api[_-]?key\s*[=:]\s*["\']?[^"\'\s]+', 'api_key=[REDACTED]'),  # API keys
    ]

    def __init__(self, timeout: int = 30, working_dir: Optional[str] = None, max_output_lines: int = 1000):
        """
        Initialize the bash tool handler.

        Args:
            timeout: Maximum execution time in seconds (default: 30)
            working_dir: Working directory for commands (default: current directory)
            max_output_lines: Maximum lines to return (default: 1000)
        """
        self.timeout = timeout
        self.working_dir = working_dir
        self.max_output_lines = max_output_lines
        self.session = BashSession(working_dir=working_dir)

    def validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Validate command for dangerous patterns.

        Args:
            command: Command to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked dangerous command pattern: {pattern}"
        return True, None

    def sanitize_output(self, output: str) -> str:
        """
        Remove sensitive data from command output.

        Args:
            output: Raw command output

        Returns:
            Sanitized output
        """
        sanitized = output
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized

    def truncate_output(self, output: str) -> str:
        """
        Truncate output to prevent token limit issues.

        Args:
            output: Command output

        Returns:
            Truncated output with summary if needed
        """
        lines = output.split('\n')
        if len(lines) <= self.max_output_lines:
            return output

        truncated_lines = lines[:self.max_output_lines]
        truncated = '\n'.join(truncated_lines)
        summary = f"\n\n[Output truncated: {len(lines)} total lines, showing first {self.max_output_lines}]"
        return truncated + summary

    def log_command(self, command: str, output: str, error: Optional[str], exit_code: int):
        """
        Log command execution for audit trails.

        Args:
            command: Command executed
            output: Command output
            error: Error output if any
            exit_code: Exit code
        """
        timestamp = datetime.now().isoformat()
        logger.info(
            f"[{timestamp}] Command: {command[:100]} | Exit: {exit_code} | "
            f"Output: {len(output)} chars | Error: {len(error) if error else 0} chars"
        )

    def execute_with_timeout(self, command: str) -> Dict[str, Any]:
        """
        Execute command with timeout protection using the session.

        Args:
            command: Command to execute

        Returns:
            Dictionary with execution results
        """
        return self.session.execute_command(command, timeout=self.timeout)

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a bash tool command from Claude with validation and sanitization.

        Args:
            tool_input: Dictionary containing 'command' and optional 'restart' flag

        Returns:
            Dictionary with command output, error (if any), and exit code
        """
        command = tool_input.get("command", "")
        restart = tool_input.get("restart", False)

        if restart:
            self.session.restart()
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

        # Validate command
        is_valid, error_msg = self.validate_command(command)
        if not is_valid:
            logger.warning(f"Blocked dangerous command: {command}")
            return {
                "error": error_msg,
                "output": "",
                "exit_code": 1
            }

        try:
            # Execute command with timeout
            result = self.execute_with_timeout(command)

            # Sanitize and truncate output
            output = result.get("output", "")
            error = result.get("error", "")
            exit_code = result.get("exit_code", 0)

            if output:
                output = self.sanitize_output(output)
                output = self.truncate_output(output)

            if error:
                error = self.sanitize_output(error)
                error = self.truncate_output(error)

            # Log command execution
            self.log_command(command, output, error, exit_code)

            # Prepare response
            response = {
                "output": output,
                "exit_code": exit_code
            }

            if error:
                response["error"] = error

            if exit_code == 0:
                response["message"] = "Command executed successfully"
            else:
                response["message"] = f"Command exited with code {exit_code}"

            return response

        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {
                "error": f"Error executing command: {str(e)}",
                "output": "",
                "exit_code": -1
            }

    def close(self):
        """Close the bash session."""
        self.session.close()


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
