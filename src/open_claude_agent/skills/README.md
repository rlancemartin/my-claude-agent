# Biomni Agent Skills

This directory contains portable Agent Skills for biomedical research tasks. These skills are designed to be self-contained and easily portable to other repositories.

## What are Agent Skills?

Agent Skills developed by Anthropic are modular capabilities that can be loaded by AI agents. Each skill contains:
- **SKILL.md**: Metadata and instructions for when/how to use the skill
- **Executable scripts**: Python or bash scripts for deterministic operations
- **Supporting files**: Additional documentation or reference materials

Learn more: [Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## Available Skills

### 📚 pubmed-search
Search PubMed database for biomedical research papers and retrieve titles, abstracts, and journal information.

**Usage:**
```bash
python skills/pubmed-search/pubmed_search.py "CRISPR gene editing" --max-papers 5
```

**Dependencies:**
```bash
pip install pymed
```

### 📄 arxiv-search
Search arXiv preprint repository for papers in physics, mathematics, computer science, quantitative biology, and related fields.

**Usage:**
```bash
python skills/arxiv-search/arxiv_search.py "protein folding prediction" --max-papers 5
```

**Dependencies:**
```bash
pip install arxiv
```

## Installation

### Quick Install (All Skills)
```bash
pip install pymed arxiv
```

### Individual Skill Installation
Each skill can be installed independently by installing its required dependencies (see skill-specific SKILL.md files).

## Testing Skills

Test each skill from the command line:

```bash
# Test PubMed search
python skills/pubmed-search/pubmed_search.py "cancer immunotherapy"

# Test arXiv search
python skills/arxiv-search/arxiv_search.py "machine learning genomics"
```

## Adding New Skills

To add a new skill:

1. Create a new directory: `skills/your-skill-name/`
2. Add a `SKILL.md` file with YAML frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: Brief description of what the skill does
   ---

   # Detailed documentation...
   ```
3. Add executable scripts (Python, Bash, etc.)
4. Update this README with the new skill

## Portability

These skills are designed to be portable:
- **Self-contained**: Each skill directory has all necessary files
- **Minimal dependencies**: Only common, well-maintained packages
- **No API keys required**: These specific skills use free, public APIs
- **Clear documentation**: SKILL.md explains usage and requirements
- **Standalone scripts**: Can be run directly from command line

You can copy any skill directory to another project and it will work independently.

## Best Practices

- Keep skills focused on a single capability
- Document all dependencies clearly
- Include usage examples in SKILL.md
- Test scripts work standalone before committing
- Use clear, descriptive skill names
