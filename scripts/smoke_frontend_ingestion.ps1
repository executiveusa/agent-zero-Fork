@echo off
REM Frontend Ingestion MCP Smoke Test (Windows PowerShell/CMD)
REM Tests the basic ingestion functionality without deployment
REM
REM Usage:
REM   .\scripts\smoke_frontend_ingestion.ps1
REM   .\scripts\smoke_frontend_ingestion.ps1 -Url "https://example.com"

echo ============================================
echo Frontend Ingestion MCP Smoke Test (Windows)
echo ============================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON=python

REM Check prerequisites
echo Checking prerequisites...

REM Check Python
where /q %PYTHON%
if errorlevel 1 (
    set PYTHON=py
    where /q %PYTHON%
    if errorlevel 1 (
        echo [ERROR] Python not found. Please install Python 3.8+
        exit /b 1
    )
)
echo [OK] Python found

REM Check playwright
%PYTHON% -c "from playwright.async_api import async_playwright" 2>nul
if errorlevel 1 (
    echo [WARNING] Playwright not installed. Installing...
    %PYTHON% -m pip install playwright
    %PYTHON% -m playwright install chromium
)
echo [OK] Playwright available

REM Check for Node.js (for Vercel/GitHub CLI)
where /q node
if errorlevel 1 (
    echo [WARNING] Node.js not found. Some deployment features may not work.
) else (
    echo [OK] Node.js found
)

REM Set default values
set TEST_URL=%1
if "%TEST_URL%"=="" set TEST_URL=https://example.com

set TEST_NAME=%2
if "%TEST_NAME%"=="" set TEST_NAME=smoke-test-example

set DEPLOY_ENABLED=%3
if "%DEPLOY_ENABLED%"=="" set DEPLOY_ENABLED=false

REM Create test output directory
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format \"yyyyMMdd_HHmmss\""') do set TIMESTAMP=%%a
set TEST_OUTPUT_DIR=%PROJECT_ROOT%\runs\smoke_test_%TIMESTAMP%
mkdir "%TEST_OUTPUT_DIR%" >nul 2>&1

echo.
echo Running smoke test...
echo URL: %TEST_URL%
echo Output: %TEST_OUTPUT_DIR%
echo.

REM Create a Python test script
echo import sys > "%TEST_OUTPUT_DIR%\test_ingest.py"
echo import asyncio >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo import json >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo from pathlib import Path >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo. >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo sys.path.insert(0, str(Path(__file__).parent.parent)) >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo from python.tools.frontend_ingestion_mcp import FrontendIngestionMCP >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo. >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo async def main(): >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     frontend = FrontendIngestionMCP() >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     print("=" * 50) >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     print("Frontend Ingestion MCP Smoke Test") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     print("=" * 50) >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     print() >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     try: >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         result = await frontend.ingest_url( >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             url="%TEST_URL%", >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             project_name="%TEST_NAME%", >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             options={ >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo                 "check_robots": False, >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo                 "download_assets": False, >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo                 "use_tailwind": False, >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             } >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         ) >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         print(f"Status: {result.get('status', 'unknown')}") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         print(f"Run ID: {result.get('run_id', 'N/A')}") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         print(f"Project Path: {result.get('project_path', 'N/A')}") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         print(f"Validation Valid: {result.get('validation', {}).get('valid', 'N/A')}") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         if result.get('status') in ['success', 'partial']: >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             print() >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             print("[PASSED] Smoke test PASSED") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             return 0 >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         else: >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             print() >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             print("[FAILED] Smoke test FAILED") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo             return 1 >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     except Exception as e: >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         print(f"Error: {e}") >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo         return 1 >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo. >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo if __name__ == "__main__": >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     exit_code = asyncio.run(main()) >> "%TEST_OUTPUT_DIR%\test_ingest.py"
echo     sys.exit(exit_code) >> "%TEST_OUTPUT_DIR%\test_ingest.py"

REM Run the test
cd "%TEST_OUTPUT_DIR%"
%PYTHON% test_ingest.py
set TEST_EXIT_CODE=%errorlevel%

REM Cleanup (optional - keep for debugging)
REM rmdir /s /q "%TEST_OUTPUT_DIR%"

echo.
if %TEST_EXIT_CODE% equ 0 (
    echo ============================================
    echo [PASSED] Smoke Test PASSED
    echo ============================================
    exit /b 0
) else (
    echo ============================================
    echo [FAILED] Smoke Test FAILED
    echo ============================================
    exit /b 1
)
