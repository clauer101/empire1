#!/bin/bash

# Run linting + type checking + unit tests for the gameserver project
# Usage: ./run_tests.sh [OPTIONS]
# Options:
#   --all          Run all tests with verbose output
#   --quick        Run tests with minimal output (default)
#   --cov          Run tests with coverage report
#   --cov-html     Generate HTML coverage report
#   --failfast     Stop on first test failure
#   --match=PATTERN  Run only tests matching PATTERN
#   --no-lint      Skip ruff + mypy (run tests only)
#   <file>         Run specific test file (e.g., tests/test_hex_math.py)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/python_server"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[0;34m'
NC='\033[0m'

VENV_PATH="$SCRIPT_DIR/.venv"
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Default options
PYTEST_OPTS="tests"
VERBOSE="-v"
COV_OPTS=""
LINT=1

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
        --no-lint)
            LINT=0
            shift
            ;;
        *)
            PYTEST_OPTS="$1"
            shift
            ;;
    esac
done

# ── 1. Ruff ──────────────────────────────────────────────────────────────────
if [[ "$LINT" -eq 1 ]]; then
    echo -e "${BLUE}[1/3] ruff check...${NC}"
    if "$VENV_PATH/bin/ruff" check python_server/src/; then
        echo -e "${GREEN}  ✓ ruff${NC}"
    else
        echo -e "${RED}  ✗ ruff failed${NC}"
        exit 1
    fi

# ── 2. mypy ──────────────────────────────────────────────────────────────────
    echo -e "${BLUE}[2/3] mypy...${NC}"
    if "$VENV_PATH/bin/mypy" python_server/src; then
        echo -e "${GREEN}  ✓ mypy${NC}"
    else
        echo -e "${RED}  ✗ mypy failed${NC}"
        exit 1
    fi
fi

# ── 3. pytest ────────────────────────────────────────────────────────────────
STEP=$( [[ "$LINT" -eq 1 ]] && echo "3/3" || echo "1/1" )
echo -e "${BLUE}[$STEP] pytest $VERBOSE $COV_OPTS $PYTEST_OPTS${NC}"

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

if pytest $VERBOSE $COV_OPTS $PYTEST_OPTS; then
    echo ""
    echo -e "${GREEN}✓ All checks passed!${NC}"
    [[ "$COV_OPTS" == *"html"* ]] && echo -e "${GREEN}  HTML coverage: $PROJECT_ROOT/htmlcov/index.html${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}✗ Some tests failed!${NC}"
    exit 1
fi
