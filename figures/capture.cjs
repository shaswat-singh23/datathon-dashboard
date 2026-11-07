// Temporary external tooling: see figures/README.md. No app dependencies change.
const { chromium } = require('playwright');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
const { statSync } = require('node:fs');

const base = process.env.FIGURES_BASE_URL || 'http://127.0.0.1:8526';
const output = resolve(__dirname);
const captures = [
  [1, 'machines', 1050, 'Manager picks surviving adjustment', ['8 / 10'], 'All machines — click a column to sort'],
  [2, 'demand', 1400, 'Coin-in per available machine-hour', ['$1,375k', '$189.0'], 'Weekday rhythm (non-event days)'],
  [3, 'downtime', 1400, 'Lost machine-hours', ['5,021', '0.38%', '$974k', '$90.7k'], 'Banks in the whole floor, ranked by share of scheduled hours lost'],
  [4, 'players', 1800, 'Tracked wagers', ['$163,804,869.65', '$148,219,409.05'], 'Concentration chart month'],
  [5, 'comps', 2100, 'Tracked comp economic cost', ['$190,669.30', '$682,749.50', '1.23%'], 'Did redemption intensity change?'],
  [6, 'actions', 1700, 'Plan cost', ['$1,200', '$98,800', '1 / 3'], 'Action drill'],
  [7, 'model', 2000, 'Lowest observed full-holdout MAE', ['$68,699/day', '$27,959.28/day higher'], null],
];

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1400 }, deviceScaleFactor: 1 });
    for (const [number, route, height, ready, expected, stopBefore] of captures) {
      await page.setViewportSize({ width: 1920, height });
      await page.goto(`${base}/${route}`);
      await page.getByText(ready, { exact: true }).first().waitFor({ timeout: 60000 });
      await page.waitForFunction(() =>
        document.querySelector('[data-testid="stApp"]')?.getAttribute('data-test-script-state') === 'notRunning',
        null, { timeout: 60000 });
      await page.locator('[data-testid="stException"]').waitFor({ state: 'hidden' });
      await page.evaluate(() => document.fonts.ready);
      const text = await page.locator('body').innerText();
      for (const value of expected) {
        if (!text.includes(value)) throw new Error(`Q${number}: missing expected ${value}`);
      }
      // Charts and dataframe canvases paint after the Streamlit script finishes.
      await page.waitForTimeout(1000);
      await page.mouse.move(1, 1);
      const file = resolve(output, `q${number}.png`);
      const boundary = stopBefore ? await page.getByText(stopBefore, { exact: true }).first().boundingBox() : null;
      if (stopBefore && (!boundary || boundary.y > height)) throw new Error(`Q${number}: section boundary is outside the viewport`);
      await page.screenshot({ path: file, clip: { x: 0, y: 0, width: 1920, height: boundary ? Math.floor(boundary.y - 16) : height } });
      if (statSync(file).size >= 1000000) throw new Error(`${file} exceeds 1 MB`);
      console.log(`Q${number}: rendered without exceptions; ${statSync(file).size} bytes`);
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(pathToFileURL(resolve(process.env.HEADLINE_HTML || '/tmp/26-headline.html')).href);
    await page.locator('.js-plotly-plot .main-svg').first().waitFor();
    await page.evaluate(() => document.fonts.ready);
    const file = resolve(output, 'headline.png');
    await page.locator('main').screenshot({ path: file });
    if (statSync(file).size >= 1000000) throw new Error(`${file} exceeds 1 MB`);
    console.log(`Headline: ${statSync(file).size} bytes`);
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
