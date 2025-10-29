"""
Text Editor Tool Handler for Claude's Text Editor Tool

This module provides a handler for Claude's text editor tool, which enables
reading and editing files in a controlled environment. The text editor tool is
client-side, meaning your application executes all file operations locally.

Usage:
    from text_editor_tool import TextEditorToolHandler

    handler = TextEditorToolHandler()
    result = handler.handle(tool_input)
"""

from pathlib import Path
import shutil
from typing import Dict, Any, Optional, List
import logging

# Set up logging
logger = logging.getLogger(__name__)


class TextEditorToolHandler:
    """
    Handler for Claude's text editor tool commands.

    Supported commands:
    - view: Read and return file contents or list directory contents
    - str_replace: Replace specific text with new content
    - create: Generate new files with content
    - insert: Add text at specific line locations
    - undo_edit: Revert last file modification (creates backups)

    Security:
        This handler implements path validation and file backups to prevent
        accidental data loss and directory traversal attacks.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the text editor tool handler.

        Args:
            base_path: Base directory for file operations (default: current directory)
                      If provided, all paths will be restricted to this directory
        """
        self.base_path = Path(base_path) if base_path else None
        self.backup_history: Dict[str, List[str]] = {}  # Track backups for undo

    def _normalize_path(self, path: str) -> Path:
        """
        Normalize and validate a file path.

        Args:
            path: The path from Claude

        Returns:
            Resolved Path object

        Raises:
            ValueError: If the path attempts to escape the base directory
        """
        path_obj = Path(path)

        # If base_path is set, ensure path stays within it
        if self.base_path:
            if path_obj.is_absolute():
                # Make it relative to base_path
                try:
                    path_obj = path_obj.relative_to(self.base_path)
                except ValueError:
                    raise ValueError(f"Path outside base directory: {path}")

            full_path = self.base_path / path_obj

            # SECURITY: Validate path stays within base_path
            try:
                full_path.resolve().relative_to(self.base_path.resolve())
            except ValueError:
                raise ValueError(f"Path traversal detected: {path}")

            return full_path
        else:
            return path_obj.resolve()

    def _create_backup(self, file_path: Path) -> Optional[str]:
        """
        Create a backup of a file before modification.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file, or None if file doesn't exist
        """
        if not file_path.exists():
            return None

        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        counter = 1
        while backup_path.exists():
            backup_path = file_path.with_suffix(f'{file_path.suffix}.backup{counter}')
            counter += 1

        shutil.copy2(file_path, backup_path)

        # Track backup for undo
        file_key = str(file_path)
        if file_key not in self.backup_history:
            self.backup_history[file_key] = []
        self.backup_history[file_key].append(str(backup_path))

        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a text editor tool command from Claude.

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
            elif command == "str_replace":
                return self._handle_str_replace(full_path, path, tool_input)
            elif command == "create":
                return self._handle_create(full_path, path, tool_input)
            elif command == "insert":
                return self._handle_insert(full_path, path, tool_input)
            elif command == "undo_edit":
                return self._handle_undo_edit(full_path, path)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            logger.error(f"Error executing {command}: {str(e)}")
            return {"error": f"Error executing {command}: {str(e)}"}

    def _handle_view(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """
        View directory contents or file contents.

        Args:
            full_path: Resolved path object
            path: Original path string
            tool_input: Tool input with optional view_range

        Returns:
            Dictionary with file/directory contents
        """
        if full_path.is_dir():
            # List directory contents
            try:
                contents = [item.name for item in full_path.iterdir()]
                return {
                    "type": "directory",
                    "contents": sorted(contents),
                    "message": f"Directory listing for {path}"
                }
            except PermissionError:
                return {"error": f"Permission denied: {path}"}
        elif full_path.is_file():
            # Read file contents
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Handle optional view_range parameter [start_line, end_line]
                view_range = tool_input.get("view_range")

                if view_range and isinstance(view_range, list) and len(view_range) == 2:
                    lines = content.split('\n')
                    start_line, end_line = view_range
                    # Claude uses 1-based line numbers
                    start = max(0, start_line - 1)
                    end = min(len(lines), end_line)
                    content = '\n'.join(lines[start:end])
                    message = f"Lines {start_line}-{end_line} of {path}"
                else:
                    message = f"File contents: {path}"

                return {
                    "type": "file",
                    "content": content,
                    "message": message
                }
            except UnicodeDecodeError:
                return {"error": f"Cannot read file (binary or encoding issue): {path}"}
            except PermissionError:
                return {"error": f"Permission denied: {path}"}
        else:
            return {"error": f"Path does not exist: {path}"}

    def _handle_str_replace(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """
        Replace specific text with new content.

        Args:
            full_path: Resolved path object
            path: Original path string
            tool_input: Tool input with old_str and new_str

        Returns:
            Dictionary with operation result
        """
        if not full_path.is_file():
            return {"error": f"File does not exist: {path}"}

        old_str = tool_input.get("old_str", "")
        new_str = tool_input.get("new_str", "")

        if not old_str:
            return {"error": "old_str parameter is required"}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Exact text matching to prevent unintended edits
            if old_str not in content:
                return {"error": f"String not found in file: {old_str[:100]}"}

            # Count occurrences
            occurrences = content.count(old_str)
            if occurrences > 1:
                logger.warning(f"Multiple occurrences found ({occurrences}), replacing first")

            # Create backup before modification
            backup_path = self._create_backup(full_path)

            # Replace first occurrence
            new_content = content.replace(old_str, new_str, 1)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            message = f"Replaced text in file: {path}"
            if backup_path:
                message += f" (backup: {backup_path})"

            return {"message": message}

        except Exception as e:
            return {"error": f"Error replacing text: {str(e)}"}

    def _handle_create(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """
        Create a new file with content.

        Args:
            full_path: Resolved path object
            path: Original path string
            tool_input: Tool input with file_text

        Returns:
            Dictionary with operation result
        """
        file_text = tool_input.get("file_text", "")

        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists and create backup
            if full_path.exists():
                backup_path = self._create_backup(full_path)
                message = f"Overwrote file: {path} (backup: {backup_path})"
            else:
                message = f"Created file: {path}"

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(file_text)

            return {"message": message}

        except Exception as e:
            return {"error": f"Error creating file: {str(e)}"}

    def _handle_insert(self, full_path: Path, path: str, tool_input: Dict) -> Dict:
        """
        Insert text at a specific line number.

        Args:
            full_path: Resolved path object
            path: Original path string
            tool_input: Tool input with insert_line and new_str

        Returns:
            Dictionary with operation result
        """
        if not full_path.is_file():
            return {"error": f"File does not exist: {path}"}

        insert_line = tool_input.get("insert_line")
        new_str = tool_input.get("new_str", "")

        if insert_line is None:
            return {"error": "insert_line parameter is required"}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Create backup before modification
            backup_path = self._create_backup(full_path)

            # Claude uses 1-based line numbers
            # Insert at the specified line (0-indexed in list)
            insert_index = max(0, min(insert_line, len(lines)))
            lines.insert(insert_index, new_str + '\n' if not new_str.endswith('\n') else new_str)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            message = f"Inserted text at line {insert_line} in: {path}"
            if backup_path:
                message += f" (backup: {backup_path})"

            return {"message": message}

        except Exception as e:
            return {"error": f"Error inserting text: {str(e)}"}

    def _handle_undo_edit(self, full_path: Path, path: str) -> Dict:
        """
        Undo the last edit by restoring from backup.

        Args:
            full_path: Resolved path object
            path: Original path string

        Returns:
            Dictionary with operation result
        """
        file_key = str(full_path)

        if file_key not in self.backup_history or not self.backup_history[file_key]:
            return {"error": f"No backup available for: {path}"}

        try:
            # Get the most recent backup
            backup_path = Path(self.backup_history[file_key].pop())

            if not backup_path.exists():
                return {"error": f"Backup file not found: {backup_path}"}

            # Restore from backup
            shutil.copy2(backup_path, full_path)

            # Remove the backup file
            backup_path.unlink()

            logger.info(f"Restored from backup: {backup_path}")
            return {"message": f"Reverted last edit to: {path}"}

        except Exception as e:
            return {"error": f"Error undoing edit: {str(e)}"}


# Convenience function for backward compatibility
def handle_text_editor_tool(tool_input: Dict[str, Any], base_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to handle text editor tool commands.

    This function creates a TextEditorToolHandler instance and processes the command.
    For better performance when handling multiple commands, create a handler instance
    and reuse it.

    Args:
        tool_input: Dictionary containing 'command' and command-specific parameters
        base_path: Optional base directory for file operations

    Returns:
        Dictionary with the result of the operation
    """
    handler = TextEditorToolHandler(base_path=base_path)
    return handler.handle(tool_input)
