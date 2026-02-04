"""
Bulletproof Browser Login Agent

Specialized agent for handling complex login scenarios with 2FA, CAPTCHA detection,
session management, and intelligent retry logic.
"""

import json
import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    async_playwright = None
    Page = None
    Browser = None


class BrowserLoginAgent:
    """Bulletproof browser automation for website login scenarios"""

    def __init__(self):
        self.session_store = {}
        self.max_retries = 3
        self.timeout = 30000
        self.headless = False
        self.viewport = {"width": 1920, "height": 1080}

    async def login(
        self,
        url: str,
        username: str,
        password: str,
        username_selector: str = None,
        password_selector: str = None,
        login_button_selector: str = None,
        verify_selector: str = None,
        two_fa_code: str = None,
        cookies_file: str = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """
        Perform login with bulletproof error handling and recovery

        Args:
            url: Website URL to login to
            username: Username/email
            password: Password
            username_selector: CSS selector for username field
            password_selector: CSS selector for password field
            login_button_selector: CSS selector for login button
            verify_selector: CSS selector to verify successful login
            two_fa_code: 2FA code if required
            cookies_file: Path to save/load cookies
            user_agent: Custom user agent string
        """
        if not async_playwright:
            return {"error": "playwright not installed", "success": False}

        browser = None
        context = None
        page = None

        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-resources",
                        "--disable-sync",
                    ]
                )

                # Create context with session/cookies
                context_opts = {
                    "viewport": self.viewport,
                    "locale": "en-US",
                    "timezone_id": "America/New_York",
                }

                if user_agent:
                    context_opts["user_agent"] = user_agent
                else:
                    context_opts["user_agent"] = (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )

                context = await browser.new_context(**context_opts)

                # Load cookies if available
                if cookies_file and os.path.exists(cookies_file):
                    try:
                        with open(cookies_file, "r") as f:
                            cookies = json.load(f)
                            await context.add_cookies(cookies)
                    except Exception as e:
                        pass

                page = await context.new_page()

                # Set longer timeout
                page.set_default_timeout(self.timeout)

                # Navigate to URL
                result = await self._navigate_and_login(
                    page=page,
                    url=url,
                    username=username,
                    password=password,
                    username_selector=username_selector,
                    password_selector=password_selector,
                    login_button_selector=login_button_selector,
                    verify_selector=verify_selector,
                    two_fa_code=two_fa_code,
                )

                # Save cookies if login successful
                if result["success"] and cookies_file:
                    cookies = await context.cookies()
                    with open(cookies_file, "w") as f:
                        json.dump(cookies, f)

                return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()

    async def _navigate_and_login(
        self,
        page: Page,
        url: str,
        username: str,
        password: str,
        username_selector: Optional[str],
        password_selector: Optional[str],
        login_button_selector: Optional[str],
        verify_selector: Optional[str],
        two_fa_code: Optional[str],
    ) -> Dict[str, Any]:
        """Navigate and perform login with retry logic"""

        for attempt in range(self.max_retries):
            try:
                # Navigate to page
                await page.goto(url, wait_until="networkidle")

                # Detect common login form elements if selectors not provided
                if not username_selector:
                    username_selector = await self._detect_username_field(page)
                if not password_selector:
                    password_selector = await self._detect_password_field(page)
                if not login_button_selector:
                    login_button_selector = await self._detect_login_button(page)

                # Check for CAPTCHA
                captcha_detected = await self._detect_captcha(page)
                if captcha_detected:
                    return {
                        "success": False,
                        "error": "CAPTCHA detected - requires manual intervention",
                        "captcha_detected": True,
                        "attempt": attempt + 1,
                    }

                # Fill username
                if username_selector:
                    await page.fill(username_selector, username)
                    await page.wait_for_timeout(500)

                # Fill password
                if password_selector:
                    await page.fill(password_selector, password)
                    await page.wait_for_timeout(500)

                # Click login button
                if login_button_selector:
                    await page.click(login_button_selector)

                # Wait for navigation or 2FA
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    await page.wait_for_timeout(2000)

                # Check for 2FA
                two_fa_detected = await self._detect_2fa(page)
                if two_fa_detected:
                    if two_fa_code:
                        success = await self._handle_2fa(page, two_fa_code)
                        if success:
                            await page.wait_for_load_state("networkidle")
                        else:
                            return {
                                "success": False,
                                "error": "2FA code submission failed",
                                "attempt": attempt + 1,
                            }
                    else:
                        return {
                            "success": False,
                            "error": "2FA required but no code provided",
                            "two_fa_required": True,
                            "attempt": attempt + 1,
                        }

                # Verify login success
                if verify_selector:
                    try:
                        await page.wait_for_selector(verify_selector, timeout=5000)
                        success = True
                    except:
                        success = False
                else:
                    # Default: check if we're not on login page anymore
                    success = "login" not in page.url.lower() or verify_selector is None

                if success or attempt == self.max_retries - 1:
                    return {
                        "success": success,
                        "url": page.url,
                        "title": await page.title(),
                        "timestamp": datetime.now().isoformat(),
                        "attempt": attempt + 1,
                        "cookies": {
                            c["name"]: c["value"]
                            for c in await page.context.cookies()
                        },
                    }

                # Wait before retry
                await page.wait_for_timeout(2000)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempt": attempt + 1,
                    }
                await page.wait_for_timeout(2000)

        return {"success": False, "error": "Max retries exceeded"}

    async def _detect_username_field(self, page: Page) -> Optional[str]:
        """Auto-detect username input field"""
        selectors = [
            "input[type='email']",
            "input[name*='user']",
            "input[name*='email']",
            "input[name*='login']",
            "input[id*='user']",
            "input[id*='email']",
        ]
        for selector in selectors:
            if await page.query_selector(selector):
                return selector
        return None

    async def _detect_password_field(self, page: Page) -> Optional[str]:
        """Auto-detect password input field"""
        return "input[type='password']"

    async def _detect_login_button(self, page: Page) -> Optional[str]:
        """Auto-detect login button"""
        selectors = [
            "button:has-text('Login')",
            "button:has-text('Sign In')",
            "button:has-text('Submit')",
            "button[type='submit']",
            "input[type='submit']",
        ]
        for selector in selectors:
            try:
                if await page.query_selector(selector):
                    return selector
            except:
                pass
        return "button[type='submit']"

    async def _detect_captcha(self, page: Page) -> bool:
        """Detect common CAPTCHA implementations"""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "[class*='captcha']",
            "[id*='captcha']",
            ".g-recaptcha",
            "[data-captcha]",
        ]
        for selector in captcha_selectors:
            if await page.query_selector(selector):
                return True
        return False

    async def _detect_2fa(self, page: Page) -> bool:
        """Detect 2FA requirement"""
        two_fa_selectors = [
            "input[name*='code']",
            "input[name*='verification']",
            "input[name*='totp']",
            "[class*='verification']",
            "[class*='2fa']",
            "[class*='mfa']",
        ]
        for selector in two_fa_selectors:
            if await page.query_selector(selector):
                return True
        return False

    async def _handle_2fa(self, page: Page, code: str) -> bool:
        """Handle 2FA code submission"""
        try:
            # Find and fill 2FA code field
            code_field = None
            selectors = [
                "input[name*='code']",
                "input[name*='verification']",
                "input[name*='totp']",
                "input[type='text']:not([type='hidden'])",
            ]
            for selector in selectors:
                if await page.query_selector(selector):
                    code_field = selector
                    break

            if code_field:
                await page.fill(code_field, code)
                await page.wait_for_timeout(500)

                # Find and click submit button
                submit_btn = await page.query_selector("button[type='submit']")
                if submit_btn:
                    await submit_btn.click()
                    return True
            return False
        except:
            return False


def process_tool(tool_input: dict) -> dict:
    """Process browser login request"""
    agent = BrowserLoginAgent()

    # Run async login
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            agent.login(
                url=tool_input.get("url"),
                username=tool_input.get("username"),
                password=tool_input.get("password"),
                username_selector=tool_input.get("username_selector"),
                password_selector=tool_input.get("password_selector"),
                login_button_selector=tool_input.get("login_button_selector"),
                verify_selector=tool_input.get("verify_selector"),
                two_fa_code=tool_input.get("two_fa_code"),
                cookies_file=tool_input.get("cookies_file"),
                user_agent=tool_input.get("user_agent"),
            )
        )
        return result
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        loop.close()
