#!/usr/bin/env python3
"""
Loveable.dev login test using PyPuppeteer (Playwright alternative)

This version works in restricted network environments by using PyPuppeteer
which doesn't require CDN-hosted browser binaries.
"""

import asyncio
import json
import sys
import time
from datetime import datetime


async def test_loveable_login_pyppeteer(email: str, password: str, attempt_num: int) -> dict:
    """
    Test Loveable.dev login using PyPuppeteer

    Args:
        email: Login email
        password: Password to try
        attempt_num: Which attempt this is (1-10)

    Returns:
        Dictionary with login results and projects
    """
    try:
        from pyppeteer import launch

        print(f"\n[ATTEMPT {attempt_num}] Starting PyPuppeteer browser...")

        # Launch browser
        browser = await launch({
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        })

        page = await browser.newPage()
        await page.setViewport({'width': 1920, 'height': 1080})

        try:
            print(f"[ATTEMPT {attempt_num}] Navigating to loveable.dev...")
            await page.goto('https://lovable.dev', {'waitUntil': 'networkidle2', 'timeout': 30000})

            # Wait a bit for page to load
            await page.waitForTimeout(2000)

            # Try to find and click login
            print(f"[ATTEMPT {attempt_num}] Looking for login button...")
            try:
                login_button = await page.querySelector('a[href*="login"]')
                if not login_button:
                    login_button = await page.querySelector('button:has-text("Sign In")')

                if login_button:
                    await login_button.click()
                    await page.waitForNavigation({'waitUntil': 'networkidle2', 'timeout': 10000})
            except:
                pass

            # Fill email
            print(f"[ATTEMPT {attempt_num}] Filling email: {email}")
            email_field = await page.querySelector('input[type="email"]')
            if email_field:
                await email_field.type(email, {'delay': 50})
                await page.waitForTimeout(500)

            # Fill password
            print(f"[ATTEMPT {attempt_num}] Filling password...")
            password_field = await page.querySelector('input[type="password"]')
            if password_field:
                await password_field.type(password, {'delay': 50})
                await page.waitForTimeout(500)

            # Click submit
            print(f"[ATTEMPT {attempt_num}] Submitting login form...")
            submit_button = await page.querySelector('button[type="submit"]')
            if not submit_button:
                submit_button = await page.querySelector('button:has-text("Sign In")')

            if submit_button:
                await submit_button.click()
                await page.waitForTimeout(3000)

            # Check if login was successful
            current_url = page.url
            print(f"[ATTEMPT {attempt_num}] Current URL: {current_url}")

            login_success = (
                "login" not in current_url.lower() and
                "signin" not in current_url.lower() and
                len(current_url) > 20
            )

            print(f"[ATTEMPT {attempt_num}] Login appears to be: {'✅ SUCCESSFUL' if login_success else '❌ FAILED'}")

            # Extract projects
            projects = []
            if login_success:
                print(f"[ATTEMPT {attempt_num}] Extracting projects...")
                await page.waitForTimeout(2000)

                # Get all text content
                content = await page.content()

                # Try to find project-like elements
                project_elements = await page.querySelectorAll('[class*="project"], [class*="card"], a[href*="project"]')

                for i, elem in enumerate(project_elements[:10]):
                    try:
                        text = await elem.textContent()
                        if text and text.strip() and len(text.strip()) > 2:
                            projects.append({
                                "name": text.strip()[:100],
                                "element": i
                            })
                    except:
                        pass

            await browser.close()

            return {
                "success": login_success,
                "email": email,
                "password": password[:1] + "*" * (len(password)-2) + password[-1],  # Mask password
                "url": current_url,
                "projects": projects[:10],
                "projects_count": len(projects),
                "timestamp": datetime.now().isoformat(),
                "method": "PyPuppeteer",
                "attempt": attempt_num,
            }

        except Exception as inner_e:
            await browser.close()
            return {
                "success": False,
                "error": f"Browser operation failed: {str(inner_e)[:100]}",
                "attempt": attempt_num,
                "timestamp": datetime.now().isoformat(),
            }

    except ImportError:
        return {
            "success": False,
            "error": "PyPuppeteer not installed",
            "attempt": attempt_num,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:200],
            "attempt": attempt_num,
            "timestamp": datetime.now().isoformat(),
        }


async def run_attempts(email: str, password1: str, password2: str, max_attempts: int = 3):
    """Run login attempts with both passwords"""
    print("=" * 80)
    print("LOVEABLE.DEV LOGIN TEST - PyPuppeteer Version")
    print("=" * 80)
    print(f"Email: {email}")
    print(f"Max attempts per password: {max_attempts}")
    print()

    results = {
        "email": email,
        "attempts": [],
        "successful_password": None,
        "timestamp": datetime.now().isoformat(),
    }

    # Try password 1
    print("[PASSWORD 1] Testing: Sheraljean1!")
    for attempt in range(1, max_attempts + 1):
        result = await test_loveable_login_pyppeteer(email, password1, attempt)
        results["attempts"].append(result)

        if result.get("success"):
            print(f"✅ SUCCESS on attempt {attempt}!")
            results["successful_password"] = password1
            results["projects_found"] = result.get("projects", [])
            return results

        if attempt < max_attempts:
            print(f"Waiting before retry {attempt + 1}...")
            await asyncio.sleep(2)

    # Try password 2
    print("\n[PASSWORD 2] Testing: Sheraljean1")
    for attempt in range(1, max_attempts + 1):
        result = await test_loveable_login_pyppeteer(email, password2, attempt)
        results["attempts"].append(result)

        if result.get("success"):
            print(f"✅ SUCCESS on attempt {attempt}!")
            results["successful_password"] = password2
            results["projects_found"] = result.get("projects", [])
            return results

        if attempt < max_attempts:
            print(f"Waiting before retry {attempt + 1}...")
            await asyncio.sleep(2)

    return results


async def main():
    """Main entry point"""
    email = "executiveusa@gmail.com"
    password1 = "Sheraljean1!"
    password2 = "Sheraljean1"

    try:
        results = await run_attempts(email, password1, password2, max_attempts=3)

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(json.dumps(results, indent=2))

        if results.get("successful_password"):
            print("\n✅ LOGIN SUCCESSFUL!")
            print(f"Working password: {results['successful_password'][:1]}****")
            print(f"Projects found: {len(results.get('projects_found', []))}")
            return 0
        else:
            print("\n❌ LOGIN FAILED - All attempts unsuccessful")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
