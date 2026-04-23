#!/usr/bin/env node
/**
 * spike-vector.mjs — dom-to-pptx 3-probe Spike
 *
 * Validates the dom-to-pptx multi-slide assembly strategy.
 * Run: node .claude/skills/design-artifact/scripts/spike-vector.mjs
 *
 * Probes:
 *   (a) Single-slide: vector-spike-single.html → #root → PPTX Blob → Buffer
 *   (b) Multi-slide: vector-spike-multi.html → 3-slide PPTX (b1 then b2 fallback)
 *   (c) Real deck: onboarding-first-week-deck/index.html → first 3 slides
 *
 * Exit codes:
 *   0  all probes passed → GO
 *   1  one or more probes failed → NO-GO
 */

import { resolve, dirname } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { createRequire } from 'module';
import { mkdirSync, writeFileSync, existsSync } from 'fs';
import { spawnSync } from 'child_process';

import JSZip from 'jszip';
import { injectDomToPptx, exportSlideBlob, mergePptxSlides } from './lib/dom-to-pptx-adapter.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(__dirname, '..');
const PROJECT_ROOT = resolve(SKILL_ROOT, '../../../');
const OUT_DIR = resolve(SKILL_ROOT, 'spike-out');

mkdirSync(OUT_DIR, { recursive: true });

const require = createRequire(import.meta.url);
const { chromium } = require(resolve(SKILL_ROOT, 'node_modules', 'playwright', 'index.js'));

// ─── Helpers ────────────────────────────────────────────────────────────────

function log(msg, ...rest) {
  const ts = new Date().toISOString().slice(11, 23);
  console.log(`[${ts}] ${msg}`, ...rest);
}

function pass(msg) { console.log(`[PASS] ${msg}`); }
function fail(msg) { console.error(`\n[FAIL] ${msg}`); }

/**
 * Write PPTX buffer to disk and validate ZIP structure using JSZip.
 * Returns { path, bytes, files: string[] }
 */
async function verifyPptxStructure(label, buf) {
  if (buf.length < 1024) {
    throw new Error(`${label}: PPTX buffer too small (${buf.length} bytes < 1KB)`);
  }

  // Validate magic bytes
  const magic = buf.slice(0, 4).toString('hex');
  if (magic !== '504b0304') {
    throw new Error(`${label}: not a valid ZIP (magic: ${magic})`);
  }

  // Parse with JSZip to enumerate files
  const zip = await JSZip.loadAsync(buf);
  const files = Object.keys(zip.files);

  if (!files.includes('ppt/slides/slide1.xml')) {
    throw new Error(`${label}: ppt/slides/slide1.xml missing. Files: ${files.slice(0, 10).join(', ')}`);
  }

  const outPath = resolve(OUT_DIR, `${label}.pptx`);
  writeFileSync(outPath, buf);
  log(`Wrote ${buf.length} bytes → ${outPath}`);

  // Optional: also run unzip -l for human-readable confirmation
  const unzipResult = spawnSync('unzip', ['-l', outPath], { encoding: 'utf8' });
  if (unzipResult.status === 0) {
    log(`ZIP listing (first 10 entries):\n${unzipResult.stdout.split('\n').slice(0, 12).join('\n')}`);
  }

  return { path: outPath, bytes: buf.length, files };
}

function countSlideFiles(files) {
  return files.filter(f => /^ppt\/slides\/slide\d+\.xml$/.test(f)).length;
}

// ─── Main ───────────────────────────────────────────────────────────────────

const results = {
  probeA: null,
  probeB: null,
  probeB_strategy: null,
  probeC: null,
  verdict: null,
};

let browser;
try {
  browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'],
  });

  // ═══════════════════════════════════════════════════════════════
  // PROBE (a): Single-slide — vector-spike-single.html → #root
  // ═══════════════════════════════════════════════════════════════
  log('\n=== PROBE (a): Single-slide ===');
  {
    const singleFixture = resolve(SKILL_ROOT, 'fixtures/vector-spike-single.html');
    const ctx = await browser.newContext({ viewport: { width: 400, height: 300 } });
    const page = await ctx.newPage();
    await page.goto(pathToFileURL(singleFixture).href, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(500);

    await injectDomToPptx(page);
    const buf = await exportSlideBlob(page, '#root', { skipDownload: true });
    const result = await verifyPptxStructure('probe-a-single', buf);

    pass(`(a) Single-slide: ${buf.length} bytes, slide1.xml present`);
    results.probeA = { status: 'PASS', bytes: buf.length, path: result.path };

    await ctx.close();
  }

  // ═══════════════════════════════════════════════════════════════
  // PROBE (b): Multi-slide — vector-spike-multi.html, 3 sections
  //   Try b1 (Array of elements) first, fall back to b2 (JSZip merge)
  // ═══════════════════════════════════════════════════════════════
  log('\n=== PROBE (b): Multi-slide ===');
  {
    const multiFixture = resolve(SKILL_ROOT, 'fixtures/vector-spike-multi.html');
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await page.goto(pathToFileURL(multiFixture).href, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);
    await injectDomToPptx(page);

    let mergedBuf = null;
    let strategyNote = '';

    // --- b1: pass NodeList/Array of elements to exportToPptx ---
    try {
      log('Trying b1: Array.from(sections) → exportToPptx(nodeArray)');
      const b1base64 = await page.evaluate(async () => {
        await new Promise(r => setTimeout(r, 300));
        const sections = Array.from(document.querySelectorAll('deck-stage section'));
        if (sections.length === 0) throw new Error('b1: no sections found');

        // Make all sections visible for simultaneous export
        sections.forEach(s => {
          s.style.display = 'flex';
          s.style.position = 'relative';
        });
        await new Promise(r => setTimeout(r, 200)); // allow layout recalc

        const blob = await window.domToPptx.exportToPptx(sections, {
          skipDownload: true,
          autoEmbedFonts: true,
        });
        if (!blob || blob.size === 0) throw new Error('b1: empty Blob returned');

        return await new Promise((resolve, reject) => {
          const fr = new FileReader();
          fr.onloadend = () => resolve(fr.result.split(',')[1]);
          fr.onerror = () => reject(new Error('FileReader failed'));
          fr.readAsDataURL(blob);
        });
      });

      mergedBuf = Buffer.from(b1base64, 'base64');
      // Validate with JSZip
      const zip = await JSZip.loadAsync(mergedBuf);
      const files = Object.keys(zip.files);
      const slideCount = countSlideFiles(files);
      log(`b1: ${mergedBuf.length} bytes, ${slideCount} slide XML(s) in ZIP`);

      if (mergedBuf.length < 1024) throw new Error(`b1: buffer too small (${mergedBuf.length})`);

      strategyNote = `b1 (Array input), ${slideCount} slide(s) in output`;
      results.probeB_strategy = 'b1';

    } catch (b1Err) {
      log(`b1 failed: ${b1Err.message}. Falling back to b2 (per-slide JSZip merge).`);

      // --- b2: per-slide individual Blobs → Node-side JSZip merge ---
      const sectionCount = await page.evaluate(() =>
        document.querySelectorAll('deck-stage section').length
      );
      log(`b2: ${sectionCount} sections found`);

      const notes = await page.evaluate(() => {
        const el = document.querySelector('script#speaker-notes[type="application/json"]');
        try { return JSON.parse(el?.textContent || '[]'); } catch { return []; }
      });

      const slideBuffers = [];
      for (let i = 0; i < sectionCount; i++) {
        log(`  b2 exporting slide ${i + 1}/${sectionCount}...`);
        await page.evaluate((idx) => {
          if (window.__deck?.goToSlide) {
            window.__deck.goToSlide(idx);
          } else {
            Array.from(document.querySelectorAll('deck-stage section')).forEach((s, j) => {
              s.setAttribute('data-active', j === idx ? 'true' : '');
              if (j !== idx) s.removeAttribute('data-active');
            });
          }
        }, i);
        await page.waitForTimeout(150);

        const buf = await exportSlideBlob(page, 'section[data-active="true"]', { skipDownload: true });
        log(`    slide ${i + 1}: ${buf.length} bytes`);
        if (buf.length < 500) throw new Error(`b2: slide ${i + 1} too small (${buf.length})`);
        slideBuffers.push(buf);
      }

      mergedBuf = await mergePptxSlides(slideBuffers, notes);
      strategyNote = `b2 (per-slide JSZip merge), ${sectionCount} slides`;
      results.probeB_strategy = 'b2';
    }

    const result = await verifyPptxStructure('probe-b-multi', mergedBuf);
    const slideCount = countSlideFiles(result.files);

    if (results.probeB_strategy === 'b2' && slideCount < 3) {
      throw new Error(`b2 merge: expected 3 slides, found ${slideCount}`);
    }

    pass(`(b) Multi-slide [${results.probeB_strategy}]: ${mergedBuf.length} bytes. ${strategyNote}`);
    results.probeB = {
      status: 'PASS',
      strategy: results.probeB_strategy,
      bytes: mergedBuf.length,
      slideCount,
      path: result.path,
      note: strategyNote,
    };

    await ctx.close();
  }

  // ═══════════════════════════════════════════════════════════════
  // PROBE (c): Real deck — onboarding-first-week-deck, first 3 slides
  // ═══════════════════════════════════════════════════════════════
  log('\n=== PROBE (c): Real deck (onboarding-first-week-deck) ===');
  {
    const realDeck = resolve(PROJECT_ROOT, 'designs/onboarding-first-week-deck/index.html');
    if (!existsSync(realDeck)) throw new Error(`Real deck not found: ${realDeck}`);

    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await page.goto(pathToFileURL(realDeck).href, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => document.fonts.ready);

    await injectDomToPptx(page);

    const allNotes = await page.evaluate(() => {
      const el = document.querySelector('script#speaker-notes[type="application/json"]');
      try { return JSON.parse(el?.textContent || '[]'); } catch { return []; }
    });
    log(`Speaker notes in real deck: ${allNotes.length}`);

    const totalSlides = await page.evaluate(() => {
      if (window.__deck?.getSlideCount) return window.__deck.getSlideCount();
      return document.querySelectorAll('deck-stage section').length;
    });
    log(`Total slides: ${totalSlides}`);

    const targetCount = Math.min(3, totalSlides);
    const slideBuffers = [];

    for (let i = 0; i < targetCount; i++) {
      log(`  Exporting slide ${i + 1}/${targetCount}...`);

      // Navigate to slide
      await page.evaluate((idx) => {
        if (window.__deck?.goToSlide) {
          window.__deck.goToSlide(idx);
        } else {
          Array.from(document.querySelectorAll('deck-stage section')).forEach((s, j) => {
            if (j === idx) s.setAttribute('data-active', 'true');
            else s.removeAttribute('data-active');
          });
        }
      }, i);

      // Apply noscale to prevent transform interference
      await page.evaluate(() => {
        document.querySelector('deck-stage')?.setAttribute('noscale', '');
      });
      await page.waitForTimeout(300);

      const buf = await exportSlideBlob(page, 'section[data-active="true"]', { skipDownload: true });
      log(`    slide ${i + 1}: ${buf.length} bytes`);
      slideBuffers.push(buf);
    }

    const notes = allNotes.slice(0, targetCount);
    const mergedBuf = await mergePptxSlides(slideBuffers, notes);
    const result = await verifyPptxStructure('probe-c-real-deck', mergedBuf);
    const slideCount = countSlideFiles(result.files);
    const hasNotes = result.files.some(f => f.startsWith('ppt/notesSlides/'));
    const hasMedia = result.files.some(f => f.startsWith('ppt/media/'));

    log(`  slides: ${slideCount}, notes: ${hasNotes}, media: ${hasMedia}`);

    pass(`(c) Real deck: ${mergedBuf.length} bytes, ${slideCount} slides, notes: ${hasNotes}, media: ${hasMedia}`);
    results.probeC = {
      status: 'PASS',
      bytes: mergedBuf.length,
      slideCount,
      hasNotes,
      hasMedia,
      path: result.path,
      totalSlidesInDeck: totalSlides,
    };

    await ctx.close();
  }

} catch (err) {
  fail(err.message);
  if (!results.probeA) results.probeA = { status: 'FAIL', error: err.message };
  else if (!results.probeB) results.probeB = { status: 'FAIL', error: err.message };
  else results.probeC = { status: 'FAIL', error: err.message };
} finally {
  if (browser) await browser.close().catch(() => {});
}

// ─── Verdict ─────────────────────────────────────────────────────────────────
const allPassed =
  results.probeA?.status === 'PASS' &&
  results.probeB?.status === 'PASS' &&
  results.probeC?.status === 'PASS';

results.verdict = allPassed ? 'GO' : 'NO_GO';

console.log('\n' + '='.repeat(60));
console.log(`SPIKE RESULT: ${results.verdict}`);
console.log('='.repeat(60));
console.log(JSON.stringify(results, null, 2));

if (!allPassed) {
  console.error('\nOne or more probes FAILED. See above for details.');
  process.exit(1);
}

console.log(`\nAll 3 probes PASSED. Adopted strategy: ${results.probeB_strategy}`);
console.log('Output files:', OUT_DIR);
process.exit(0);
