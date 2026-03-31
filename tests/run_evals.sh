#!/bin/bash
# Run skill evaluations using pytest
# Based on Deep Agents methodology

set -e

echo "============================================"
echo "Skill Evaluation Runner"
echo "Based on Deep Agents Methodology"
echo "============================================"
echo ""

# Change to skills directory
cd "$(dirname "$0")"

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found"
    echo "Install with: pip install pytest"
    exit 1
fi

# Default options
SKILL=""
MARKERS=""
VERBOSE="-v"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skill)
            SKILL="$2"
            shift 2
            ;;
        --baseline-only)
            MARKERS="-m baseline"
            shift
            ;;
        --skill-only)
            MARKERS="-m skill"
            shift
            ;;
        --quiet)
            VERBOSE=""
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skill NAME         Run tests for specific skill"
            echo "  --baseline-only      Run only baseline tests"
            echo "  --skill-only         Run only skill tests"
            echo "  --quiet              Reduce output verbosity"
            echo "  --help               Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                   # Run all tests"
            echo "  $0 --skill bmi-report  # Test only bmi-report"
            echo "  $0 --baseline-only   # Run baseline tests only"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build test path
if [ -n "$SKILL" ]; then
    TEST_PATH="skills/test_${SKILL//-/_}.py"
else
    TEST_PATH="skills/"
fi

# Run pytest
echo "Running tests..."
echo "Test path: $TEST_PATH"
echo "Markers: ${MARKERS:-all tests}"
echo ""

pytest $VERBOSE $MARKERS $TEST_PATH

EXIT_CODE=$?

# Aggregate results if tests passed
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "Aggregating Results..."
    echo "============================================"
    python3 skills/aggregate_results.py
fi

echo ""
echo "============================================"
echo "Evaluation Complete"
echo "============================================"

exit $EXIT_CODE
