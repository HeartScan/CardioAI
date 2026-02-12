import fs from "node:fs";
import path from "node:path";
import { test, expect } from "@playwright/test";

function loadBackendExample(index) {
  const repoRoot = path.resolve(process.cwd(), "..");
  const p = path.join(repoRoot, "resp_example", "heart_rate_first10_responses.json");
  const raw = fs.readFileSync(p, "utf-8");
  const records = JSON.parse(raw);
  if (!Array.isArray(records)) throw new Error("Expected JSON array in heart_rate_first10_responses.json");
  if (index < 0 || index >= records.length) throw new Error(`Index out of range: ${index} (len=${records.length})`);
  return records[index];
}

test("UI initializes dialog with backend example record", async ({ page }) => {
  const obsIndex = Number.parseInt(process.env.OBS_INDEX || "0", 10);
  const record = loadBackendExample(obsIndex);

  // Intercept the UI init call and replace the payload with our selected backend record.
  await page.route("**/api/init", async (route) => {
    const req = route.request();
    const headers = { ...req.headers(), "content-type": "application/json" };
    const postData = JSON.stringify({ observation: record });
    const resp = await route.fetch({ headers, postData, method: "POST" });
    await route.fulfill({ response: resp });
  });

  await page.goto("/", { waitUntil: "domcontentloaded" });

  // The app appends the first assistant message after /api/init returns.
  const firstAssistant = page.locator(".msg.assistant").first();
  await expect(firstAssistant).toContainText("I am CardioAI", { timeout: 120_000 });

  // Optional pause for manual interactive debugging:
  // E2E_PAUSE=1 will keep the browser open so you can continue chatting.
  if ((process.env.E2E_PAUSE || "").trim() === "1") {
    await page.pause();
  }
});

