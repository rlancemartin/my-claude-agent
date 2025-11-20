---
name: pubmed-search
description: Search PubMed database for biomedical research papers and retrieve titles, abstracts, and journal information
---

# PubMed Search Skill

This skill provides access to the PubMed database, which contains over 35 million citations for biomedical literature from MEDLINE, life science journals, and online books.

## When to Use This Skill

Use this skill when you need to:
- Find research papers on biomedical topics
- Retrieve abstracts and metadata for scientific publications
- Search for papers by topic, disease, drug, protein, or any biomedical concept
- Get recent publications on a specific research area

## How to Use

The skill provides a Python script that searches PubMed and returns formatted results.

### Basic Usage

```bash
python ./skills/pubmed-search/pubmed_search.py "your search query" [--max-papers N]
```

**Arguments:**
- `query` (required): The search query string (e.g., "CRISPR gene editing", "COVID-19 vaccines")
- `--max-papers` (optional): Maximum number of papers to retrieve (default: 10)

### Examples

Search for papers on a specific topic:
```bash
python ./skills/pubmed-search/pubmed_search.py "machine learning drug discovery" --max-papers 5
```

Search for disease-related papers:
```bash
python ./skills/pubmed-search/pubmed_search.py "alzheimer disease biomarkers"
```

Search for specific proteins or genes:
```bash
python ./skills/pubmed-search/pubmed_search.py "TP53 mutations cancer"
```

## Output Format

The script returns formatted results with:
- **Title**: Paper title
- **Abstract**: Full abstract text
- **Journal**: Journal name where published

Each paper is separated by blank lines for readability.

## Features

- **Smart retry logic**: Automatically simplifies queries if no results found
- **Rate limiting**: Built-in delays to respect PubMed API guidelines
- **Error handling**: Clear error messages for troubleshooting
- **No API key required**: Free access to PubMed database

## Dependencies

Requires the `pymed` Python package:
```bash
pip install pymed
```

## Notes

- PubMed searches work best with specific biomedical terminology
- Results are sorted by relevance
- The tool respects NCBI's rate limiting guidelines
- If no results found, the query is automatically simplified and retried
