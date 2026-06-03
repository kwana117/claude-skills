/**
 * Template Playwright para capturar provas de UI.
 *
 * Adaptar:
 * - URL, EMAIL, PASS para o projecto
 * - Adicionar uma secção "Captura N" por cada print necessário
 * - Cada secção navega → espera → screenshot (fullPage:false ou clip)
 *
 * Output para /tmp/<projecto>-proof/ui-<descricao>.png
 * Depois o add-captions.py consome esses ficheiros.
 *
 * Correr: cd /tmp/<projecto>-proof && node capture-ui.mjs
 * Requer: npm i playwright (no folder) + npx playwright install chromium
 */
import { chromium } from "playwright";

const URL = "https://EXAMPLE.PRODUCTION.URL";   // EDITAR
const EMAIL = "EDITAR@example.com";             // EDITAR
const PASS = "EDITAR";                          // EDITAR
const OUTDIR = "/tmp/PROJECTO-proof";           // EDITAR

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
const page = await ctx.newPage();

// Login
await page.goto(`${URL}/login`);
await page.fill('input[type="email"]', EMAIL);
await page.fill('input[type="password"]', PASS);
await Promise.all([
  page.waitForURL(/dashboard|home|painel/, { timeout: 15000 }),
  page.click('button[type="submit"]'),
]);
await page.waitForLoadState("networkidle");

// Captura 1: elemento pequeno (sidebar, header)
await page.screenshot({
  path: `${OUTDIR}/ui-sidebar.png`,
  clip: { x: 0, y: 0, width: 320, height: 130 },
});
console.log("ok sidebar");

// Captura 2: página completa + scroll até ao alvo
await page.goto(`${URL}/EDITAR/PATH`);
await page.waitForLoadState("networkidle");
await page.waitForTimeout(800);

const target = page.locator('text=/elemento alvo/i').first();
if (await target.isVisible({ timeout: 3000 }).catch(() => false)) {
  const box = await target.boundingBox();
  if (box) await page.evaluate((y) => window.scrollTo(0, Math.max(0, y - 200)), box.y);
  await page.waitForTimeout(400);
}
await page.screenshot({ path: `${OUTDIR}/ui-pagina-x.png`, fullPage: false });
console.log("ok pagina-x");

await browser.close();
console.log("done");
