"""
Skill loader for progressive disclosure of agent skills.

Based on Anthropic's skills architecture:
https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SkillLoader:
    """
    Loads and manages agent skills from a directory structure.

    Skills follow this structure:
    skills/
    ├── skill-name/
    │   ├── SKILL.md      # Required: contains YAML frontmatter with name and description
    │   ├── reference.md  # Optional: additional documentation
    │   └── script.py     # Optional: executable scripts

    Progressive disclosure operates across three levels:
    1. Metadata (name + description) loaded into system prompt
    2. Full SKILL.md content read when skill is relevant
    3. Additional files and scripts accessed as needed
    """

    def __init__(self, skills_dir: str = "./skills"):
        """
        Initialize the skill loader.

        Args:
            skills_dir: Path to directory containing skills (default: ./skills)
        """
        self.skills_dir = Path(skills_dir)
        self.skills: List[Dict[str, str]] = []

    def load_skills(self) -> List[Dict[str, str]]:
        """
        Scan the skills directory and load metadata from all valid skills.

        Returns:
            List of skill dictionaries with keys: name, description, path
        """
        self.skills = []

        if not self.skills_dir.exists():
            return self.skills

        if not self.skills_dir.is_dir():
            return self.skills

        # Scan for subdirectories containing SKILL.md
        for item in self.skills_dir.iterdir():
            if not item.is_dir():
                continue

            skill_file = item / "SKILL.md"
            if not skill_file.exists():
                continue

            # Parse metadata from SKILL.md
            metadata = self._parse_skill_metadata(skill_file)
            if metadata:
                # Store full path to skill directory (for agent to use)
                metadata["path"] = str(item)
                self.skills.append(metadata)

        return self.skills

    def _parse_skill_metadata(self, skill_file: Path) -> Optional[Dict[str, str]]:
        """
        Parse YAML frontmatter from a SKILL.md file to extract metadata.

        Expected format:
        ---
        name: skill-name
        description: Brief description of the skill
        ---

        Args:
            skill_file: Path to SKILL.md file

        Returns:
            Dictionary with name and description, or None if parsing fails
        """
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML frontmatter between --- delimiters
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not frontmatter_match:
                return None

            frontmatter = frontmatter_match.group(1)

            # Parse simple YAML (name and description only)
            metadata = {}
            for line in frontmatter.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Match "key: value" format
                match = re.match(r'^(\w+):\s*(.+)$', line)
                if match:
                    key, value = match.groups()
                    metadata[key] = value.strip()

            # Validate required fields
            if 'name' not in metadata or 'description' not in metadata:
                return None

            return {
                'name': metadata['name'],
                'description': metadata['description']
            }

        except Exception:
            return None

    def format_skills_for_system_message(self) -> str:
        """
        Format loaded skills into a section for the system message.

        This provides Level 1 progressive disclosure: just metadata.
        Claude can then read full SKILL.md files when needed (Level 2).

        Returns:
            Formatted string to inject into system message
        """
        if not self.skills:
            return ""

        lines = ["# Available Skills", ""]
        lines.append("You have access to the following skills. Each skill contains specialized knowledge and tools.")
        lines.append("To use a skill, read its SKILL.md file for detailed instructions.")
        lines.append("")

        for skill in self.skills:
            lines.append(f"**{skill['name']}**")
            lines.append(f"- Description: {skill['description']}")
            lines.append(f"- Location: `{skill['path']}/SKILL.md`")
            lines.append("")

        return "\n".join(lines)

    def get_skill_names(self) -> List[str]:
        """
        Get a list of all loaded skill names.

        Returns:
            List of skill names
        """
        return [skill['name'] for skill in self.skills]


def load_skills(skills_dir: str = "./skills") -> str:
    """
    Convenience function to load skills and return formatted system message section.

    Args:
        skills_dir: Path to directory containing skills (default: ./skills)

    Returns:
        Formatted skills section for system message, or empty string if no skills
    """
    loader = SkillLoader(skills_dir)
    loader.load_skills()
    return loader.format_skills_for_system_message()
