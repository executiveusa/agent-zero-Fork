#!/bin/bash
#
# Loveable.dev Login Test - Hostinger VPS Solution
# Run this script on your Hostinger VPS to test login with full network access
#
# Usage: bash run_loveable_test_hostinger.sh
#

set -e

echo "========================================================================"
echo "LOVEABLE.DEV LOGIN TEST - HOSTINGER VPS SOLUTION"
echo "========================================================================"
echo ""
echo "This script will:"
echo "  1. Install required Python packages"
echo "  2. Run Loveable.dev login test"
echo "  3. Extract first 10 projects"
echo "  4. Save results to JSON"
echo ""

# Configuration
EMAIL="executiveusa@gmail.com"
PASSWORD1="Sheraljean1!"
PASSWORD2="Sheraljean1"
RESULTS_FILE="/root/loveable_login_results.json"
LOG_FILE="/root/loveable_login_test.log"

echo "[STEP 1] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    apt-get update -qq
    apt-get install -y python3 python3-pip 2>&1 | tail -3
else
    echo "✅ Python3 found: $(python3 --version)"
fi

echo ""
echo "[STEP 2] Installing required packages..."
pip install -q playwright requests beautifulsoup4 2>&1 | tail -3

echo ""
echo "[STEP 3] Installing Chromium browser..."
python3 -m playwright install chromium 2>&1 | tail -5

echo ""
echo "[STEP 4] Running Loveable.dev login test..."

python3 << 'PYTHON_SCRIPT'
import asyncio
import json
import sys
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

async def test_login(email, password, attempt):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            print(f"[Attempt {attempt}] Navigating to loveable.dev...")
            await page.goto("https://lovable.dev", timeout=30000)

            # Look for login button
            login_button = await page.query_selector("a:has-text('Sign In')")
            if not login_button:
                login_button = await page.query_selector("[href*='login']")

            if login_button:
                print(f"[Attempt {attempt}] Clicking login button...")
                await login_button.click()
                await page.wait_for_load_state("networkidle")

            # Fill form
            email_field = await page.query_selector("input[type='email']")
            if email_field:
                print(f"[Attempt {attempt}] Entering email...")
                await email_field.fill(email)
                await page.wait_for_timeout(500)

            password_field = await page.query_selector("input[type='password']")
            if password_field:
                print(f"[Attempt {attempt}] Entering password...")
                await password_field.fill(password)
                await page.wait_for_timeout(500)

            # Submit
            submit = await page.query_selector("button[type='submit']")
            if not submit:
                submit = await page.query_selector("button:has-text('Sign In')")

            if submit:
                print(f"[Attempt {attempt}] Submitting...")
                await submit.click()
                await page.wait_for_timeout(3000)

            # Check success
            url = page.url
            success = "login" not in url.lower() and "signin" not in url.lower()

            # Extract projects
            projects = []
            if success:
                print(f"[Attempt {attempt}] ✅ Login successful! Extracting projects...")
                elements = await page.query_selector_all("[class*='project'], [class*='card']")
                for elem in elements[:10]:
                    try:
                        text = await elem.text_content()
                        if text and len(text.strip()) > 2:
                            projects.append(text.strip()[:100])
                    except:
                        pass

            await browser.close()

            return {
                "success": success,
                "url": url,
                "projects": projects,
                "attempt": attempt
            }

        except Exception as e:
            await browser.close()
            return {"success": False, "error": str(e)[:100], "attempt": attempt}

async def main():
    email = "executiveusa@gmail.com"
    password1 = "Sheraljean1!"
    password2 = "Sheraljean1"

    results = {"email": email, "timestamp": datetime.now().isoformat(), "attempts": []}

    # Try password 1
    print("\n[PASSWORD 1] Testing: Sheraljean1!")
    for i in range(1, 4):
        result = await test_login(email, password1, i)
        results["attempts"].append(result)
        if result.get("success"):
            results["successful_password"] = password1
            results["projects_found"] = result.get("projects", [])
            break
        if i < 3:
            await asyncio.sleep(2)

    # Try password 2 if first failed
    if not results.get("successful_password"):
        print("\n[PASSWORD 2] Testing: Sheraljean1")
        for i in range(1, 4):
            result = await test_login(email, password2, i+3)
            results["attempts"].append(result)
            if result.get("success"):
                results["successful_password"] = password2
                results["projects_found"] = result.get("projects", [])
                break
            if i < 3:
                await asyncio.sleep(2)

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(json.dumps(results, indent=2))

    # Save to file
    with open("/root/loveable_login_results.json", "w") as f:
        json.dump(results, f, indent=2)

    if results.get("successful_password"):
        print(f"\n✅ SUCCESS! Working password: {results['successful_password'][:1]}****")
        print(f"Projects found: {len(results.get('projects_found', []))}")
        return 0
    else:
        print("\n❌ FAILED - No successful login")
        return 1

exit_code = asyncio.run(main())
sys.exit(exit_code)

PYTHON_SCRIPT

echo ""
echo "[STEP 5] Test complete!"
if [ -f "$RESULTS_FILE" ]; then
    echo "Results saved to: $RESULTS_FILE"
    echo ""
    echo "Results:"
    cat "$RESULTS_FILE"
else
    echo "No results file created"
fi

echo ""
echo "========================================================================"
echo "To transfer results to your local machine, use:"
echo "scp root@<hostinger-ip>:/root/loveable_login_results.json ."
echo "========================================================================"
