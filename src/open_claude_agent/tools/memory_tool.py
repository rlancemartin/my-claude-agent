"""
Memory Tool Handler for Claude's Memory Tool

This module provides a handler for Claude's memory tool, which enables persistent
storage of information across conversations. The memory tool is client-side,
meaning your application executes all file operations locally.

Usage:
    from memory_tool import MemoryToolHandler

    handler = MemoryToolHandler(base_path="./scratchpad")
    result = handler.handle(tool_input)
"""

from pathlib import Path
import shutil
from typing import Dict, Any

class MemoryToolHandler:
    """
    Handler for Claude's memory tool commands.

    Supported commands:
    - view: Display directory or file contents
    - create: Create or overwrite a file
    - str_replace: Replace text within a file
    - insert: Insert text at a specific line
    - delete: Delete a file or directory
    - rename: Rename or move a file/directory

    Security:
        This handler implements basic path validation to prevent directory traversal.
        In production environments, additional security measures should be implemented.
    """

    def __init__(self):
        """
        Initialize the memory tool handler.

        The handler uses a hardcoded ./memories directory for all memory storage.
        """
        self.base_path = Path("./memories")
        self.base_path.mkdir(exist_ok=True)

    def _normalize_path(self, path: str) -> Path:
        """
        Normalize a memory path to a filesystem path.

        Claude uses /memories or /scratchpad as a virtual root. This method:
        1. Removes the virtual root prefix if present (e.g., /memories, /scratchpad)
        2. Resolves the path relative to the base_path
        3. Validates the path stays within base_path (security)

        Args:
            path: The path from Claude (e.g., "/memories/file.txt" or "/scratchpad/file.txt")

        Returns:
            Resolved Path object

        Raises:
            ValueError: If the path attempts to escape the base directory
        """
        # Remove leading virtual root paths
        for prefix in ["/memories", "/scratchpad"]:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break

        if path.startswith("/"):
            path = path[1:]

        # Resolve to actual filesystem path
        full_path = self.base_path / path if path else self.base_path

        # SECURITY: Validate path stays within base_path
        try:
            full_path.resolve().relative_to(self.base_path.resolve())
        except ValueError:
            raise ValueError(f"Path traversal detected: {path}")

        return full_path

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a memory tool command from Claude.

        Args:
            tool_input: Dictionary containing 'command' and command-specific parameters

        Returns:
            Dictionary with the result of the operation
        """
        command = tool_input.get("command")
        path = tool_input.get("path", "")

        try:
            full_path = self._normalize_path(path)

            if command == "view":
                return self._handle_view(full_path, path, tool_input)
            elif command == "create":
                return self._handle_create(full_path, path, tool_input)
            elif command == "str_replace":
                return self._handle_str_replace(full_path, path, tool_input)
            elif command == "insert":
                return self._handle_insert(full_path, path, tool_input)
            elif command == "delete":
                return self._handle_delete(full_path, path, tool_input)
            elif command == "rename":
                return self._handle_rename(full_path, path, tool_input)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Error executing {command}: {str(e)}"}

    def _handle_view(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """View directory contents or file contents."""
        if full_path.is_dir():
            # List directory contents
            contents = [item.name for item in full_path.iterdir()]
            return {
                "type": "directory",
                "contents": contents,
                "message": f"Directory listing for {path or '/'}"
            }
        elif full_path.is_file():
            # Read file contents
            with open(full_path, 'r') as f:
                content = f.read()

            # Handle optional line range parameters
            start_line = tool_input.get("start_line")
            end_line = tool_input.get("end_line")

            if start_line or end_line:
                lines = content.split('\n')
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                content = '\n'.join(lines[start:end])

            return {
                "type": "file",
                "content": content,
                "message": f"File contents: {path}"
            }
        else:
            return {"error": f"Path does not exist: {path}"}

    def _handle_create(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """
        Create or overwrite a file.

        According to the official docs, the parameter name is 'file_text':
        https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool
        """
        file_text = tool_input.get("file_text", "")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(file_text)
        return {"message": f"Created file: {path}"}

    def _handle_str_replace(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """Replace text within a file."""
        if not full_path.is_file():
            return {"error": f"File does not exist: {path}"}

        old_str = tool_input.get("old_str", "")
        new_str = tool_input.get("new_str", "")

        with open(full_path, 'r') as f:
            content = f.read()

        if old_str not in content:
            return {"error": f"String not found in file: {old_str}"}

        # Replace first occurrence
        new_content = content.replace(old_str, new_str, 1)

        with open(full_path, 'w') as f:
            f.write(new_content)

        return {"message": f"Replaced text in file: {path}"}

    def _handle_insert(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """Insert text at a specific line number."""
        if not full_path.is_file():
            return {"error": f"File does not exist: {path}"}

        line_number = tool_input.get("line_number", 1)
        text = tool_input.get("text", "")

        with open(full_path, 'r') as f:
            lines = f.readlines()

        # Insert at the specified line (1-indexed)
        lines.insert(line_number - 1, text + '\n')

        with open(full_path, 'w') as f:
            f.writelines(lines)

        return {"message": f"Inserted text at line {line_number} in: {path}"}

    def _handle_delete(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """Delete a file or directory."""
        if full_path.is_file():
            full_path.unlink()
            return {"message": f"Deleted file: {path}"}
        elif full_path.is_dir():
            shutil.rmtree(full_path)
            return {"message": f"Deleted directory: {path}"}
        else:
            return {"error": f"Path does not exist: {path}"}

    def _handle_rename(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """Rename or move a file/directory."""
        new_path = tool_input.get("new_path", "")
        new_full_path = self._normalize_path(new_path)

        new_full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.rename(new_full_path)

        return {"message": f"Renamed {path} to {new_path}"}


# Convenience function for backward compatibility
def handle_memory_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to handle memory tool commands.

    This function creates a MemoryToolHandler instance and processes the command.
    For better performance when handling multiple commands, create a handler instance
    and reuse it.

    Args:
        tool_input: Dictionary containing 'command' and command-specific parameters

    Returns:
        Dictionary with the result of the operation
    """
    handler = MemoryToolHandler()
    return handler.handle(tool_input)
