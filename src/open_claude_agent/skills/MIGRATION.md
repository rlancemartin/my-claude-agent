# Migration Guide

This guide explains how to move these skills to a new repository or project.

## What You're Moving

The `skills/` directory is completely self-contained and portable:

```
skills/
├── README.md                          # Overview of all skills
├── QUICKSTART.md                      # Quick start guide
├── MIGRATION.md                       # This file
├── requirements.txt                   # All Python dependencies
├── arxiv-search/
│   ├── SKILL.md                      # Skill metadata and docs
│   └── arxiv_search.py               # Executable script
└── pubmed-search/
    ├── SKILL.md                      # Skill metadata and docs
    └── pubmed_search.py              # Executable script
```

## Migration Steps

### Option 1: Copy the Entire Directory (Recommended)

```bash
# From your new project root
cp -r /path/to/Biomni/skills ./

# Install dependencies
pip install -r skills/requirements.txt

# Test
python3 skills/pubmed-search/pubmed_search.py "test query"
```

### Option 2: Copy Individual Skills

If you only want specific skills:

```bash
# Create skills directory in new project
mkdir -p skills

# Copy just the skills you want
cp -r /path/to/Biomni/skills/pubmed-search ./skills/
cp -r /path/to/Biomni/skills/arxiv-search ./skills/

# Copy the top-level docs (optional but helpful)
cp /path/to/Biomni/skills/README.md ./skills/
cp /path/to/Biomni/skills/QUICKSTART.md ./skills/

# Install only needed dependencies
pip install pymed  # for pubmed-search
pip install arxiv  # for arxiv-search
```

### Option 3: Git Subtree (For Ongoing Sync)

If you want to keep skills synced with the source repo:

```bash
# Add as subtree
git subtree add --prefix=skills https://github.com/your-org/Biomni.git main:skills --squash

# Later, to update
git subtree pull --prefix=skills https://github.com/your-org/Biomni.git main:skills --squash
```

## Verification Checklist

After migration, verify everything works:

- [ ] Skills directory exists in new location
- [ ] All SKILL.md files are present
- [ ] Python scripts are executable (`chmod +x skills/*//*.py`)
- [ ] Dependencies installed (`pip install -r skills/requirements.txt`)
- [ ] Scripts run from command line
- [ ] Claude Code can discover the skills (if using Claude Code)

## Testing After Migration

```bash
# Test PubMed search
python3 skills/pubmed-search/pubmed_search.py "cancer" --max-papers 2

# Test arXiv search
python3 skills/arxiv-search/arxiv_search.py "machine learning" --max-papers 2
```

Expected output: Formatted paper titles and abstracts.

## Integration with Different Agents

### Claude Code
Place in `skills/` directory at project root. Claude will auto-discover.

### Custom Agents
1. Point your agent to the `skills/` directory
2. Have it read SKILL.md files for metadata
3. Execute Python scripts via subprocess/CLI calls

### Direct Usage
Scripts can be called directly from any Python code:

```python
import subprocess

result = subprocess.run(
    ["python3", "skills/pubmed-search/pubmed_search.py", "CRISPR", "--max-papers", "5"],
    capture_output=True,
    text=True
)
print(result.stdout)
```

## Dependencies Management

### Virtual Environment (Recommended)
```bash
cd your-new-project
python3 -m venv venv
source venv/bin/activate
pip install -r skills/requirements.txt
```

### System-Wide Installation
```bash
pip install -r skills/requirements.txt
```

### Poetry
```bash
# Add to pyproject.toml
poetry add pymed arxiv
```

### Conda
```bash
conda install -c conda-forge pymed
pip install arxiv  # Not available in conda
```

## Customization After Migration

Each skill can be customized independently:

1. **Modify search parameters**: Edit the Python scripts to change defaults
2. **Add new features**: Extend the scripts with additional functionality
3. **Update documentation**: Edit SKILL.md to reflect your changes
4. **Add new skills**: Follow the same pattern to create additional skills

## Troubleshooting

### Scripts not executable
```bash
chmod +x skills/*/*.py
```

### Import errors
```bash
pip install -r skills/requirements.txt
```

### Python version compatibility
These skills require Python 3.7+. Check your version:
```bash
python3 --version
```

## No External Dependencies

These skills have NO dependencies on:
- The Biomni codebase
- Specific directory structures
- API keys or authentication
- External databases or files
- The original repository

They are truly portable!

## License

These skills inherit the license from the Biomni project. If moving to a different licensed project, ensure compatibility.
