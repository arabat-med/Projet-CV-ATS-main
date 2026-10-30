// Vérification sur l'application réelle : aucune réponse API n'est simulée.
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const [inputs, screenshots] = process.argv.slice(2);
  if (!inputs || !screenshots) throw new Error('Usage: node scripts/check_browser.cjs INPUTS SCREENSHOTS');
  const output = path.resolve(screenshots);
  const baseUrl = process.env.CV_BASE_URL || 'http://127.0.0.1:5173';
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ channel: process.env.CV_BROWSER_CHANNEL || 'chrome' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  try {
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(output, '01-accueil.png'), fullPage: true });
    await page.goto(`${baseUrl}/start`);
    await page.screenshot({ path: path.join(output, '02-import.png'), fullPage: true });
    await page.locator('input[type=file]').first().setInputFiles(path.resolve(inputs, 'cv-demo.docx'));
    const analysis = page.waitForResponse((r) => r.url().endsWith('/api/cv/analyze') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Analyser le CV', exact: true }).click();
    const response = await analysis;
    assert.equal(response.status(), 200);
    const result = await response.json();
    assert.equal(result.contact.email, 'demo@example.invalid');
    await page.getByText('CV reconstitué (vue synthèse)', { exact: false }).waitFor();
    await page.screenshot({ path: path.join(output, '03-extraction.png'), fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1800 });
    await page.locator('.result-section').scrollIntoViewIfNeeded();
    await page.locator('.result-section').screenshot({ path: path.join(output, '08-resultat-detail.png') });
    await page.setViewportSize({ width: 1440, height: 1000 });
    const jsonDownload = page.waitForEvent('download');
    await page.getByRole('button', { name: 'JSON', exact: true }).click();
    await (await jsonDownload).saveAs(path.resolve(inputs, 'resultat-interface.json'));
    // Le chemin PDF texte est exercé avec un second téléversement réel.
    await page.locator('input[type=file]').first().setInputFiles(path.resolve(inputs, 'cv-demo.pdf'));
    const pdfAnalysis = page.waitForResponse((r) => r.url().endsWith('/api/cv/analyze') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Analyser le CV', exact: true }).click();
    assert.equal((await pdfAnalysis).status(), 200);
    await page.goto(`${baseUrl}/normalize`);
    await page.locator('input[type=file]').setInputFiles(path.resolve(__dirname, '../examples/cv-ancien.json'));
    const normalization = page.waitForResponse((r) => r.url().endsWith('/api/cv/normalize') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Normaliser le CV', exact: true }).click();
    assert.equal((await normalization).status(), 200);
    await page.getByText('Normalisation réussie !').waitFor();
    await page.screenshot({ path: path.join(output, '04-normalisation.png'), fullPage: true });
    for (const extension of ['DOCX', 'PDF']) {
      const downloaded = page.waitForEvent('download');
      await page.getByRole('button', { name: `Télécharger ${extension}`, exact: true }).click();
      await (await downloaded).saveAs(path.resolve(inputs, `normalise.${extension.toLowerCase()}`));
    }
    await page.goto(`${baseUrl}/example`);
    await page.getByRole('button', { name: 'Format JSON', exact: true }).click();
    await page.screenshot({ path: path.join(output, '05-exemple-json.png'), fullPage: true });
    await page.goto(baseUrl);
    await page.getByRole('button', { name: 'Toggle Dark Mode', exact: true }).click();
    assert.equal(await page.locator('html').getAttribute('class'), 'dark');
    await page.screenshot({ path: path.join(output, '06-theme-sombre.png'), fullPage: true });
    await page.getByRole('button', { name: 'Toggle Dark Mode', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Ouvrir le menu', exact: true }).click();
    await page.getByRole('link', { name: 'Normaliser un CV', exact: true }).click();
    await page.getByRole('heading', { name: 'Normaliser votre CV', exact: false }).waitFor();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.screenshot({ path: path.join(output, '07-mobile.png'), fullPage: true });
    assert.deepEqual(errors, []);
    console.log('Parcours réels vérifiés : DOCX, PDF texte, JSON, normalisation, exports, thème et navigation mobile.');
    console.log('Captures enregistrées dans', output);
  } finally {
    await context.close();
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
