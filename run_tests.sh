#!/bin/bash
#
# Simple test runner for Open Claude Agent integration tests
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Open Claude Agent Integration Tests"
echo "========================================"
echo ""

# Check for ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}ERROR: ANTHROPIC_API_KEY environment variable is not set${NC}"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your_key_here'"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ ANTHROPIC_API_KEY is set${NC}"
echo ""

# Install/update dependencies
echo "Installing dependencies..."
uv sync
echo ""

# Run pytest
echo "Running tests..."
echo ""
uv run pytest tests/ -v

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
