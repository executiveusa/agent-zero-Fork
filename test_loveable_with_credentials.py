#!/usr/bin/env python3
"""
Loveable.dev Login Test with Credentials
Works with Docker and Hostinger VPS
"""

import asyncio
import json
import os
import sys
from datetime import datetime


async def test_loveable_login(email: str, password: str, attempt_num: int) -> dict:
    """Test Loveable.dev login"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {
            "success": False,
            "error": "Playwright not installed",
            "attempt": attempt_num
        }

    async with async_playwright() as p:
        browser = None
        try:
            print(f"[Attempt {attempt_num}] Launching browser...")
            browser = await p.chromium.launch(headless=True)

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            print(f"[Attempt {attempt_num}] Navigating to loveable.dev...")
            await page.goto("https://lovable.dev", timeout=30000)
            await page.wait_for_timeout(2000)

            # Find and click login
            print(f"[Attempt {attempt_num}] Finding login button...")
            login_btn = None
            selectors = ["a:has-text('Sign In')", "[href*='login']", "button:has-text('Login')"]
            for selector in selectors:
                try:
                    login_btn = await page.query_selector(selector)
                    if login_btn:
                        break
                except:
                    pass

            if login_btn:
                print(f"[Attempt {attempt_num}] Clicking login...")
                await login_btn.click()
                await page.wait_for_timeout(2000)

            # Fill email
            print(f"[Attempt {attempt_num}] Entering email...")
            email_field = await page.query_selector("input[type='email']")
            if email_field:
                await email_field.fill(email)
                await page.wait_for_timeout(500)

            # Fill password
            print(f"[Attempt {attempt_num}] Entering password...")
            password_field = await page.query_selector("input[type='password']")
            if password_field:
                await password_field.fill(password)
                await page.wait_for_timeout(500)

            # Submit
            print(f"[Attempt {attempt_num}] Submitting form...")
            submit_btn = None
            submit_selectors = ["button[type='submit']", "button:has-text('Sign In')"]
            for selector in submit_selectors:
                try:
                    submit_btn = await page.query_selector(selector)
                    if submit_btn:
                        break
                except:
                    pass

            if submit_btn:
                await submit_btn.click()
                await page.wait_for_timeout(3000)

            # Check URL
            url = page.url
            success = (
                "login" not in url.lower() and
                "signin" not in url.lower() and
                len(url) > 20
            )

            print(f"[Attempt {attempt_num}] URL: {url}")
            print(f"[Attempt {attempt_num}] Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

            # Extract projects
            projects = []
            if success:
                print(f"[Attempt {attempt_num}] Extracting projects...")
                await page.wait_for_timeout(2000)

                selectors_to_try = [
                    "[class*='project']",
                    "[class*='card']",
                    "a[href*='project']",
                    "[role='link']"
                ]

                for selector in selectors_to_try:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            try:
                                text = await elem.text_content()
                                if text and len(text.strip()) > 3:
                                    projects.append(text.strip()[:100])
                            except:
                                pass
                        if projects:
                            break
                    except:
                        pass

                # Remove duplicates
                projects = list(set(projects))[:10]
                print(f"[Attempt {attempt_num}] Found {len(projects)} projects")

            await context.close()
            await browser.close()

            return {
                "success": success,
                "email": email,
                "password_masked": password[:1] + "*" * (len(password)-2) + password[-1],
                "url": url,
                "projects": projects,
                "projects_count": len(projects),
                "timestamp": datetime.now().isoformat(),
                "attempt": attempt_num
            }

        except Exception as e:
            if browser:
                await browser.close()
            print(f"[Attempt {attempt_num}] Error: {str(e)[:100]}")
            return {
                "success": False,
                "error": str(e)[:200],
                "attempt": attempt_num,
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Main function"""
    email = os.getenv("EMAIL", "executiveusa@gmail.com")
    password1 = os.getenv("PASSWORD1", "")
    password2 = os.getenv("PASSWORD2", "")

    if not password1 or not password2:
        print("ERROR: Set PASSWORD1 and PASSWORD2 environment variables")
        return 1

    print("=" * 80)
    print("LOVEABLE.DEV LOGIN TEST WITH CREDENTIALS")
    print("=" * 80)
    print(f"Email: {email}")
    print()

    results = {
        "email": email,
        "timestamp": datetime.now().isoformat(),
        "attempts": [],
        "successful_password": None,
        "projects_found": []
    }

    # Try password 1 (max 3 attempts)
    print("[PASSWORD 1] Testing...")
    for attempt in range(1, 4):
        result = await test_loveable_login(email, password1, attempt)
        results["attempts"].append(result)

        if result.get("success"):
            print(f"\n✅ SUCCESS on attempt {attempt}!")
            results["successful_password"] = password1
            results["projects_found"] = result.get("projects", [])
            print(f"Projects found: {len(results['projects_found'])}")
            for project in results["projects_found"][:5]:
                print(f"  - {project}")
            break

        if attempt < 3:
            print(f"Waiting before retry {attempt + 1}...")
            await asyncio.sleep(3)

    # Try password 2 if first didn't work
    if not results["successful_password"]:
        print("\n[PASSWORD 2] Testing...")
        for attempt in range(4, 7):
            result = await test_loveable_login(email, password2, attempt)
            results["attempts"].append(result)

            if result.get("success"):
                print(f"\n✅ SUCCESS on attempt {attempt}!")
                results["successful_password"] = password2
                results["projects_found"] = result.get("projects", [])
                print(f"Projects found: {len(results['projects_found'])}")
                for project in results["projects_found"][:5]:
                    print(f"  - {project}")
                break

            if attempt < 6:
                print(f"Waiting before retry {attempt + 1}...")
                await asyncio.sleep(3)

    # Print and save results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(json.dumps(results, indent=2))

    # Save to file
    output_file = "/results/loveable_login_results.json"
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    except:
        # Fallback to current directory
        with open("loveable_login_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: loveable_login_results.json")

    if results["successful_password"]:
        print(f"\n✅✅ LOGIN SUCCESSFUL!")
        print(f"Working password: {results['successful_password'][:1]}****")
        print(f"Total projects extracted: {len(results['projects_found'])}")
        return 0
    else:
        print(f"\n❌ LOGIN FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
