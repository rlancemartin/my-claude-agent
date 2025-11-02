"""
Unit tests for the skill loader module.

These tests verify skill discovery, metadata parsing, and formatting
without requiring the Anthropic API.
"""

import os
import tempfile
from pathlib import Path
import pytest

from open_claude_agent.skill_loader import SkillLoader, load_skills


@pytest.fixture
def temp_skills_dir(tmp_path):
    """Create a temporary skills directory for testing."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir


@pytest.fixture
def valid_skill(temp_skills_dir):
    """Create a valid skill with proper YAML frontmatter."""
    skill_dir = temp_skills_dir / "test-skill"
    skill_dir.mkdir()

    skill_content = """---
name: test-skill
description: A test skill for unit testing
---

# Test Skill

This is a test skill used in unit tests.

## Usage

Instructions for using this skill.
"""

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(skill_content)

    return skill_dir


@pytest.fixture
def skill_with_script(temp_skills_dir):
    """Create a skill with an accompanying Python script."""
    skill_dir = temp_skills_dir / "scripted-skill"
    skill_dir.mkdir()

    skill_content = """---
name: scripted-skill
description: Skill with executable script
---

# Scripted Skill

This skill includes a Python script.

## Using the Script

```bash
python skills/scripted-skill/process.py --input data.txt
```
"""

    script_content = """#!/usr/bin/env python3
print("Test script executed")
"""

    (skill_dir / "SKILL.md").write_text(skill_content)
    (skill_dir / "process.py").write_text(script_content)

    return skill_dir


@pytest.fixture
def invalid_skill_no_frontmatter(temp_skills_dir):
    """Create a skill without YAML frontmatter."""
    skill_dir = temp_skills_dir / "invalid-skill"
    skill_dir.mkdir()

    skill_content = """# Invalid Skill

This skill is missing YAML frontmatter.
"""

    (skill_dir / "SKILL.md").write_text(skill_content)
    return skill_dir


@pytest.fixture
def invalid_skill_missing_fields(temp_skills_dir):
    """Create a skill with incomplete frontmatter."""
    skill_dir = temp_skills_dir / "incomplete-skill"
    skill_dir.mkdir()

    skill_content = """---
name: incomplete-skill
---

# Incomplete Skill

Missing description field.
"""

    (skill_dir / "SKILL.md").write_text(skill_content)
    return skill_dir


class TestSkillLoader:
    """Test cases for SkillLoader class."""

    def test_init(self, temp_skills_dir):
        """Test SkillLoader initialization."""
        loader = SkillLoader(str(temp_skills_dir))
        assert loader.skills_dir == Path(str(temp_skills_dir))
        assert loader.skills == []

    def test_load_valid_skill(self, temp_skills_dir, valid_skill):
        """Test loading a valid skill."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 1
        assert skills[0]['name'] == 'test-skill'
        assert skills[0]['description'] == 'A test skill for unit testing'
        assert 'path' in skills[0]

    def test_load_multiple_skills(self, temp_skills_dir, valid_skill, skill_with_script):
        """Test loading multiple skills."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 2
        skill_names = [s['name'] for s in skills]
        assert 'test-skill' in skill_names
        assert 'scripted-skill' in skill_names

    def test_load_skill_with_script(self, temp_skills_dir, skill_with_script):
        """Test loading a skill that includes a script."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 1
        assert skills[0]['name'] == 'scripted-skill'
        assert skills[0]['description'] == 'Skill with executable script'

        # Verify the script exists
        script_path = skill_with_script / "process.py"
        assert script_path.exists()

    def test_load_skills_empty_directory(self, temp_skills_dir):
        """Test loading from an empty skills directory."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert skills == []

    def test_load_skills_nonexistent_directory(self):
        """Test loading from a non-existent directory."""
        loader = SkillLoader("./nonexistent_skills_dir")
        skills = loader.load_skills()

        assert skills == []

    def test_skip_invalid_skill_no_frontmatter(self, temp_skills_dir, invalid_skill_no_frontmatter):
        """Test that skills without frontmatter are skipped."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 0

    def test_skip_invalid_skill_missing_fields(self, temp_skills_dir, invalid_skill_missing_fields):
        """Test that skills with incomplete frontmatter are skipped."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 0

    def test_mixed_valid_invalid_skills(self, temp_skills_dir, valid_skill, invalid_skill_no_frontmatter):
        """Test that only valid skills are loaded when mixed with invalid ones."""
        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 1
        assert skills[0]['name'] == 'test-skill'

    def test_skip_non_directory_items(self, temp_skills_dir, valid_skill):
        """Test that non-directory items in skills folder are ignored."""
        # Create a file in the skills directory (not a subdirectory)
        (temp_skills_dir / "readme.txt").write_text("Not a skill")

        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        # Should only load the valid skill directory, not the file
        assert len(skills) == 1
        assert skills[0]['name'] == 'test-skill'

    def test_skip_directory_without_skill_md(self, temp_skills_dir, valid_skill):
        """Test that directories without SKILL.md are ignored."""
        # Create a directory without SKILL.md
        empty_dir = temp_skills_dir / "empty-skill"
        empty_dir.mkdir()

        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        # Should only load the valid skill
        assert len(skills) == 1
        assert skills[0]['name'] == 'test-skill'


class TestSkillFormatting:
    """Test cases for skill formatting."""

    def test_format_single_skill(self, temp_skills_dir, valid_skill):
        """Test formatting a single skill for system message."""
        loader = SkillLoader(str(temp_skills_dir))
        loader.load_skills()
        formatted = loader.format_skills_for_system_message()

        assert "# Available Skills" in formatted
        assert "test-skill" in formatted
        assert "A test skill for unit testing" in formatted
        assert "SKILL.md" in formatted

    def test_format_multiple_skills(self, temp_skills_dir, valid_skill, skill_with_script):
        """Test formatting multiple skills."""
        loader = SkillLoader(str(temp_skills_dir))
        loader.load_skills()
        formatted = loader.format_skills_for_system_message()

        assert "test-skill" in formatted
        assert "scripted-skill" in formatted
        # Check that both skills have their paths included
        assert formatted.count("/test-skill/SKILL.md") == 1
        assert formatted.count("/scripted-skill/SKILL.md") == 1

    def test_format_empty_skills(self, temp_skills_dir):
        """Test formatting when no skills are loaded."""
        loader = SkillLoader(str(temp_skills_dir))
        loader.load_skills()
        formatted = loader.format_skills_for_system_message()

        assert formatted == ""

    def test_get_skill_names(self, temp_skills_dir, valid_skill, skill_with_script):
        """Test retrieving skill names."""
        loader = SkillLoader(str(temp_skills_dir))
        loader.load_skills()
        names = loader.get_skill_names()

        assert len(names) == 2
        assert 'test-skill' in names
        assert 'scripted-skill' in names


class TestConvenienceFunction:
    """Test cases for the load_skills convenience function."""

    def test_load_skills_function(self, temp_skills_dir, valid_skill):
        """Test the load_skills convenience function."""
        formatted = load_skills(str(temp_skills_dir))

        assert "# Available Skills" in formatted
        assert "test-skill" in formatted
        assert "A test skill for unit testing" in formatted

    def test_load_skills_function_empty(self, temp_skills_dir):
        """Test load_skills with empty directory."""
        formatted = load_skills(str(temp_skills_dir))

        assert formatted == ""

    def test_load_skills_function_nonexistent(self):
        """Test load_skills with non-existent directory."""
        formatted = load_skills("./nonexistent_dir")

        assert formatted == ""


class TestYAMLParsing:
    """Test cases for YAML frontmatter parsing."""

    def test_parse_with_extra_whitespace(self, temp_skills_dir):
        """Test parsing YAML with extra whitespace."""
        skill_dir = temp_skills_dir / "whitespace-skill"
        skill_dir.mkdir()

        skill_content = """---

name:   whitespace-skill
description:    Skill with extra whitespace

---

# Content
"""

        (skill_dir / "SKILL.md").write_text(skill_content)

        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        assert len(skills) == 1
        assert skills[0]['name'] == 'whitespace-skill'
        assert skills[0]['description'] == 'Skill with extra whitespace'

    def test_parse_multiline_description(self, temp_skills_dir):
        """Test that multiline descriptions only capture the first line."""
        skill_dir = temp_skills_dir / "multiline-skill"
        skill_dir.mkdir()

        # Multiline descriptions will only capture the first line
        skill_content = """---
name: multiline-skill
description: This is a
  multiline description
---

# Content
"""

        (skill_dir / "SKILL.md").write_text(skill_content)

        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        # Parser captures only first line of description
        assert len(skills) == 1
        assert skills[0]['name'] == 'multiline-skill'
        assert skills[0]['description'] == 'This is a'  # Only first line captured

    def test_parse_with_additional_fields(self, temp_skills_dir):
        """Test parsing YAML with extra fields (should be ignored)."""
        skill_dir = temp_skills_dir / "extra-fields-skill"
        skill_dir.mkdir()

        skill_content = """---
name: extra-fields-skill
description: Skill with extra fields
author: Test Author
version: 1.0.0
---

# Content
"""

        (skill_dir / "SKILL.md").write_text(skill_content)

        loader = SkillLoader(str(temp_skills_dir))
        skills = loader.load_skills()

        # Should successfully parse, just ignore extra fields
        assert len(skills) == 1
        assert skills[0]['name'] == 'extra-fields-skill'
        assert skills[0]['description'] == 'Skill with extra fields'
        # Extra fields not included in result
        assert 'author' not in skills[0]
        assert 'version' not in skills[0]
