#!/bin/bash
#
# Frontend Ingestion MCP Smoke Test
# Tests the basic ingestion functionality
#
# Usage:
#   ./scripts/smoke_frontend_ingestion.sh [webflow_url] [project_name]
#
# Examples:
#   ./scripts/smoke_frontend_ingestion.sh
#   ./scripts/smoke_frontend_ingestion.sh https://your-project.webflow.io my-webflow-site
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-python3}"

# Default test URL (Webflow project - replace with your URL)
TEST_URL="${1:-https://example.com}"
TEST_NAME="${2:-webflow-test}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Frontend Ingestion MCP Smoke Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if ! command -v $PYTHON &> /dev/null; then
    echo -e "${RED}❌ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $($PYTHON --version)${NC}"

# Check playwright
echo -e "${YELLOW}Checking Playwright...${NC}"
if ! $PYTHON -c "from playwright.async_api import async_playwright" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Playwright not installed. Installing...${NC}"
    $PYTHON -m pip install playwright
    $PYTHON -m playwright install chromium
fi
echo -e "${GREEN}✓ Playwright available${NC}"

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}⚠ pnpm not found. Trying npm...${NC}"
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ Neither pnpm nor npm found. Some validation features may not work.${NC}"
    fi
fi

# Create test output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_OUTPUT_DIR="$PROJECT_ROOT/runs/smoke_test_$TIMESTAMP"
mkdir -p "$TEST_OUTPUT_DIR"

echo ""
echo -e "${YELLOW}Running smoke test...${NC}"
echo -e "${YELLOW}URL: $TEST_URL${NC}"
echo -e "${YELLOW}Project Name: $TEST_NAME${NC}"
echo -e "${YELLOW}Output: $TEST_OUTPUT_DIR${NC}"
echo ""

# Create a simple Python test script
cat > "$TEST_OUTPUT_DIR/test_ingest.py" << EOF
#!/usr/bin/env python3
"""Simple smoke test for frontend ingestion."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.tools.frontend_ingestion_mcp import FrontendIngestionMCP


async def main():
    frontend = FrontendIngestionMCP()
    
    print("=" * 50)
    print("Frontend Ingestion MCP Smoke Test")
    print("=" * 50)
    print()
    
    try:
        # Test ingestion with Webflow URL
        result = await frontend.ingest_url(
            url="$TEST_URL",
            project_name="$TEST_NAME",
            options={
                "check_robots": False,  # Disable for test
                "download_assets": False,  # Keep it simple
                "use_tailwind": False,
            }
        )
        
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Run ID: {result.get('run_id', 'N/A')}")
        print(f"Project Path: {result.get('project_path', 'N/A')}")
        print(f"Snapshot Path: {result.get('snapshot_path', 'N/A')}")
        print(f"React Path: {result.get('react_path', 'N/A')}")
        print()
        
        validation = result.get('validation', {})
        print(f"Validation Valid: {validation.get('valid', 'N/A')}")
        
        if validation.get('errors'):
            print("Validation Errors:")
            for error in validation['errors']:
                print(f"  - {error}")
        
        errors = result.get('errors', [])
        if errors:
            print()
            print("Errors:")
            for error in errors:
                print(f"  - {error}")
        
        # Write result to file
        report_file = Path(result.get('project_path', '.')) / 'smoke_test_report.json'
        if report_file.parent.exists():
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print()
            print(f"Report written to: {report_file}")
        
        if result.get('status') in ['success', 'partial']:
            print()
            print("✓ Smoke test PASSED")
            return 0
        else:
            print()
            print("✗ Smoke test FAILED")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
EOF

# Run the test
cd "$TEST_OUTPUT_DIR"
$PYTHON test_ingest.py
TEST_EXIT_CODE=$?

# Show results location
echo ""
echo "========================================"
echo "Test Output Directory: $TEST_OUTPUT_DIR"
echo "========================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Smoke Test PASSED${NC}"
else
    echo -e "${RED}✗ Smoke Test FAILED${NC}"
fi

echo ""
echo "To run with your Webflow project:"
echo "  ./scripts/smoke_frontend_ingestion.sh https://your-project.webflow.io your-project-name"
echo ""

exit $TEST_EXIT_CODE
