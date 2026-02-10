#!/bin/bash

# Run unit tests for the gameserver project
# Usage: ./run_tests.sh [OPTIONS]
# Options:
#   --all          Run all tests with verbose output
#   --quick        Run tests with minimal output (default)
#   --cov          Run tests with coverage report
#   --cov-html     Generate HTML coverage report
#   --failfast     Stop on first test failure
#   --match=PATTERN  Run only tests matching PATTERN
#   <file>         Run specific test file (e.g., tests/test_hex_math.py)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists
VENV_PATH="$PROJECT_ROOT/../.venv"
if [ -d "$VENV_PATH" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source "$VENV_PATH/bin/activate"
fi

cd "$PROJECT_ROOT"

# Set PYTHONPATH to include local src directory (for development)
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Default pytest options
PYTEST_OPTS="tests"
VERBOSE="-v"
COV_OPTS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            VERBOSE="-vv"
            shift
            ;;
        --quick)
            VERBOSE="-q"
            shift
            ;;
        --cov)
            COV_OPTS="--cov=gameserver --cov-report=term-missing"
            shift
            ;;
        --cov-html)
            COV_OPTS="--cov=gameserver --cov-report=html --cov-report=term-missing"
            shift
            ;;
        --failfast)
            PYTEST_OPTS="$PYTEST_OPTS -x"
            shift
            ;;
        --match=*)
            PATTERN="${1#--match=}"
            PYTEST_OPTS="$PYTEST_OPTS -k $PATTERN"
            shift
            ;;
        *)
            # Assume it's a test file or pattern
            PYTEST_OPTS="$1"
            shift
            ;;
    esac
done

echo -e "${BLUE}Running pytest in: $PROJECT_ROOT${NC}"
echo -e "${BLUE}PYTHONPATH: $PYTHONPATH${NC}"
echo -e "${BLUE}Command: pytest $VERBOSE $COV_OPTS $PYTEST_OPTS${NC}"
echo ""

# Run pytest
if pytest $VERBOSE $COV_OPTS $PYTEST_OPTS; then
    EXIT_CODE=$?
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    if [[ "$COV_OPTS" == *"html"* ]]; then
        echo -e "${GREEN}✓ HTML coverage report generated in: htmlcov/index.html${NC}"
    fi
    
    exit 0
else
    EXIT_CODE=$?
    echo ""
    echo -e "${YELLOW}✗ Some tests failed!${NC}"
    exit $EXIT_CODE
fi
