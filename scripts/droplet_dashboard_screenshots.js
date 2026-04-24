/**
 * Run on droplet with: cd /tmp/dashproof && source /root/stock-bot/.env && node /path/to/droplet_dashboard_screenshots.js
 * Requires: npm install puppeteer (in cwd or NODE_PATH)
 */
const puppeteer = require("puppeteer");
const path = require("path");
const outDir = process.env.DASH_SHOT_DIR || "/tmp/dash_screens";

(async () => {
  const user = process.env.DASHBOARD_USER;
  const pass = process.env.DASHBOARD_PASS;
  if (!user || !pass) {
    console.error("Missing DASHBOARD_USER / DASHBOARD_PASS");
    process.exit(1);
  }
  const fs = require("fs");
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });
  await page.authenticate({ username: user, password: pass });
  await page.goto("http://127.0.0.1:5000/", { waitUntil: "networkidle2", timeout: 120000 });
  await page.waitForSelector(".container", { timeout: 60000 });
  await new Promise((r) => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(outDir, "01_home_disclaimer.png"), fullPage: true });

  async function openMoreAndClick(labelSubstr) {
    await page.click(".tab[data-tab='more']");
    await new Promise((r) => setTimeout(r, 400));
    const clicked = await page.evaluate((sub) => {
      const buttons = Array.from(document.querySelectorAll("#more-dropdown-content button"));
      const b = buttons.find((x) => (x.textContent || "").includes(sub));
      if (b) {
        b.click();
        return true;
      }
      return false;
    }, labelSubstr);
    if (!clicked) throw new Error("Could not click: " + labelSubstr);
    await new Promise((r) => setTimeout(r, 2500));
  }

  await openMoreAndClick("Telemetry");
  await page.screenshot({ path: path.join(outDir, "02_telemetry.png"), fullPage: true });

  await page.click("button.tab[data-tab='system_health']");
  await new Promise((r) => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(outDir, "03_system_health.png"), fullPage: true });

  await openMoreAndClick("Fast-Lane");
  await new Promise((r) => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(outDir, "04_fast_lane.png"), fullPage: true });

  await browser.close();
  console.log("OK", outDir);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
