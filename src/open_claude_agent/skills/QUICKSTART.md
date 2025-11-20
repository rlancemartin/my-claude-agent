# Quick Start Guide

## Installation

Install all skill dependencies at once:

```bash
pip install -r skills/requirements.txt
```

Or install individually:

```bash
# For PubMed search
pip install pymed

# For arXiv search
pip install arxiv
```

## Testing the Skills

### PubMed Search

```bash
# Basic search
python3 skills/pubmed-search/pubmed_search.py "CRISPR gene editing"

# Limit results
python3 skills/pubmed-search/pubmed_search.py "cancer immunotherapy" --max-papers 5

# Search for specific diseases
python3 skills/pubmed-search/pubmed_search.py "alzheimer disease biomarkers"
```

### arXiv Search

```bash
# Basic search
python3 skills/arxiv-search/arxiv_search.py "protein folding"

# Limit results
python3 skills/arxiv-search/arxiv_search.py "machine learning genomics" --max-papers 5

# Search computational biology
python3 skills/arxiv-search/arxiv_search.py "single cell RNA-seq analysis"
```

## Using with Claude Code

Claude Code will automatically discover these skills if they're in the `skills/` directory. Claude will:

1. See the skill names and descriptions in its system prompt
2. Load the full SKILL.md when the skill is relevant to the task
3. Execute the Python scripts when needed to perform searches

### Example Prompts for Claude

```
"Search PubMed for recent papers on CRISPR-Cas9 applications"

"Find arXiv papers about deep learning for protein structure prediction"

"Use the PubMed skill to find research on mRNA vaccines"
```

## Moving to a New Repository

To use these skills in another project:

1. **Copy the entire skills directory**:
   ```bash
   cp -r skills /path/to/new/project/
   ```

2. **Install dependencies**:
   ```bash
   cd /path/to/new/project
   pip install -r skills/requirements.txt
   ```

3. **Test the skills**:
   ```bash
   python3 skills/pubmed-search/pubmed_search.py "test query"
   ```

That's it! The skills are completely self-contained.

## Troubleshooting

### "command not found: python"
Use `python3` instead of `python`:
```bash
python3 skills/pubmed-search/pubmed_search.py "query"
```

### "package not installed" error
Install the required package:
```bash
pip install pymed arxiv
```

### No results found
- Try simpler, more general queries
- Use standard biomedical terminology
- For PubMed: The tool will automatically retry with simplified queries
- For arXiv: Try adding field prefixes like "q-bio" or "cs.LG"

### Rate limiting
Both APIs have rate limits. If you encounter errors:
- Add delays between requests
- Reduce the number of max_papers
- Wait a few minutes before retrying
