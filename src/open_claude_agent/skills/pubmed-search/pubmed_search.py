#!/usr/bin/env python3
"""
PubMed Search Tool

Searches the PubMed database for biomedical research papers.
"""

import argparse
import sys
import time


def query_pubmed(query: str, max_papers: int = 10, max_retries: int = 3) -> str:
    """Query PubMed for papers based on the provided search query.

    Parameters
    ----------
    query : str
        The search query string.
    max_papers : int
        The maximum number of papers to retrieve (default: 10).
    max_retries : int
        Maximum number of retry attempts with modified queries (default: 3).

    Returns
    -------
    str
        The formatted search results or an error message.
    """
    try:
        from pymed import PubMed
    except ImportError:
        return "Error: pymed package not installed. Install with: pip install pymed"

    try:
        pubmed = PubMed(tool="BiomniSkill", email="skill@example.com")

        # Initial attempt
        papers = list(pubmed.query(query, max_results=max_papers))

        # Retry with modified queries if no results
        retries = 0
        while not papers and retries < max_retries:
            retries += 1
            # Simplify query with each retry by removing the last word
            simplified_query = " ".join(query.split()[:-retries]) if len(query.split()) > retries else query
            time.sleep(1)  # Add delay between requests
            papers = list(pubmed.query(simplified_query, max_results=max_papers))

        if papers:
            results = "\n\n".join(
                [f"Title: {paper.title}\nAbstract: {paper.abstract}\nJournal: {paper.journal}" for paper in papers]
            )
            return results
        else:
            return "No papers found on PubMed after multiple query attempts."
    except Exception as e:
        return f"Error querying PubMed: {e}"


def main():
    parser = argparse.ArgumentParser(description="Search PubMed for biomedical research papers")
    parser.add_argument("query", type=str, help="Search query string")
    parser.add_argument(
        "--max-papers", type=int, default=10, help="Maximum number of papers to retrieve (default: 10)"
    )

    args = parser.parse_args()

    result = query_pubmed(args.query, max_papers=args.max_papers)
    print(result)


if __name__ == "__main__":
    main()
