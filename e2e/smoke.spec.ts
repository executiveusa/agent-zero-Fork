import { test, expect } from "@playwright/test";

test("agent zero home page loads", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Agent Zero/i);
  await expect(page.locator("body")).toContainText(/Agent Zero/i);
});
