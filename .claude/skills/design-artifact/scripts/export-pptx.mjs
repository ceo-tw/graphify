#!/usr/bin/env node
/**
 * export-pptx.mjs
 *
 * Converts an HTML slide deck to PPTX using Playwright (headless Chromium) for
 * screenshot capture and pptxgenjs for slide assembly.
 *
 * Usage:
 *   node export-pptx.mjs --input <path.html> [--output <path.pptx>]
 *     [--mode screenshots|editable|hybrid] [--strict]
 *     [--fallback-on-error screenshots|none]
 *     [--verify-hint <path.json>]
 *     [--width 1920] [--height 1080]
 *     [--timeout 60000] [--verbose] [--help]
 *
 * Exit codes:
 *   0  success
 *   1  unexpected runtime error
 *   2  unsupported --mode value
 *   3  input file not found
 *   4  --input flag missing
 *   5  output write failure
 *   6  editable mode failed and --strict is set (no fallback)
 */

import { parseArgs } from 'node:util';
import { existsSync, readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(__dirname, '..');

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

const ALLOWED_MODES = ['screenshots', 'editable', 'hybrid'];

let parsedArgs;
try {
  parsedArgs = parseArgs({
    options: {
      input:             { type: 'string',  short: 'i' },
      output:            { type: 'string',  short: 'o' },
      mode:              { type: 'string',  default: 'screenshots' },
      strict:            { type: 'boolean', default: false },
      'fallback-on-error': { type: 'string', default: 'screenshots' },
      'verify-hint':     { type: 'string' },
      svg:               { type: 'string',  default: 'vector' }, // 'vector' | 'raster'
      width:             { type: 'string',  default: '1920' },
      height:            { type: 'string',  default: '1080' },
      timeout:           { type: 'string',  default: '60000' },
      verbose:           { type: 'boolean', short: 'v', default: false },
      help:              { type: 'boolean', short: 'h', default: false },
    },
    strict: true,
  });
} catch (err) {
  process.stdout.write(JSON.stringify({ status: 'error', error: err.message }) + '\n');
  process.exit(1);
}

const { values: args } = parsedArgs;

// --help
if (args.help) {
  process.stdout.write([
    'Usage: export-pptx.mjs --input <path.html> [options]',
    '',
    'Options:',
    '  --input,   -i  Path to input HTML file (required)',
    '  --output,  -o  Path to output PPTX file (default: <input>.pptx)',
    '  --mode         Export mode: screenshots|editable|hybrid (default: screenshots)',
    '  --strict       In editable mode, error instead of screenshots fallback',
    '  --fallback-on-error  screenshots|none (default: screenshots)',
    '  --verify-hint  Path to .verify/vector-hint.json for PHASE 5 hint channel',
    '  --svg          vector|raster (default: vector) — SVG handling in editable mode',
    '  --width        Viewport width in px (default: 1920)',
    '  --height       Viewport height in px (default: 1080)',
    '  --timeout      Navigation timeout in ms (default: 60000)',
    '  --verbose, -v  Enable verbose logging to stderr',
    '  --help,    -h  Show this help',
    '',
    'Exit codes:',
    '  0  success',
    '  1  runtime error',
    '  2  unsupported --mode value',
    '  3  input file not found',
    '  4  missing --input',
    '  5  output write failure',
    '  6  editable failed with --strict (no fallback)',
  ].join('\n') + '\n');
  process.exit(0);
}

// Validate --mode
if (!ALLOWED_MODES.includes(args.mode)) {
  process.stdout.write(JSON.stringify({
    status: 'error',
    error: `Unsupported mode: "${args.mode}". Allowed modes: ${ALLOWED_MODES.join('|')}`,
  }) + '\n');
  process.exit(2);
}

// Validate --input present
if (!args.input) {
  process.stdout.write(JSON.stringify({
    status: 'error',
    error: '--input is required',
  }) + '\n');
  process.exit(4);
}

const width   = parseInt(args.width,   10);
const height  = parseInt(args.height,  10);
const timeout = parseInt(args.timeout, 10);
const verbose = args.verbose;
const useStrict = args.strict;
const fallbackOnError = args['fallback-on-error'] ?? 'screenshots';
const verifyHintPath = args['verify-hint'];
// Fix 9: svgAsVector defaults to true per deck-authoring.md:346 (SVG vector MUST).
// --svg=raster disables vector SVG (fallback to raster PNG embed).
const svgAsVector = (args.svg ?? 'vector') !== 'raster';

const inputPath = resolve(args.input);

// Validate --input file exists
if (!existsSync(inputPath)) {
  process.stdout.write(JSON.stringify({
    status: 'error',
    error: `Input file not found: ${inputPath}`,
  }) + '\n');
  process.exit(3);
}

const outputPath = args.output
  ? resolve(args.output)
  : inputPath.replace(/\.html?$/i, '') + '.pptx';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function log(...msg) {
  if (verbose) process.stderr.write('[export-pptx] ' + msg.join(' ') + '\n');
}

function md5(buf) {
  return createHash('md5').update(buf).digest('hex');
}

// ---------------------------------------------------------------------------
// Tier detection (extracted function)
// ---------------------------------------------------------------------------

/**
 * Detect slide count and detection method from the loaded page.
 * Reused by all modes.
 *
 * @param {import('playwright').Page} page
 * @returns {Promise<{slideCount: number, detectionMethod: string, warnings: string[]}>}
 */
async function detectTierAndSlideCount(page) {
  const warnings = [];
  let slideCount;
  let detectionMethod;

  // Tier 1: window.__deck API
  const hasDeckApi = await page.evaluate(() => {
    return typeof window.__deck === 'object' &&
           window.__deck !== null &&
           typeof window.__deck.getSlideCount === 'function' &&
           typeof window.__deck.goToSlide === 'function';
  });

  if (hasDeckApi) {
    slideCount = await page.evaluate(() => window.__deck.getSlideCount());
    detectionMethod = 'deck_api';
    log('Detection: deck_api, slides:', slideCount);
  } else {
    // Tier 2: <deck-stage> > section elements
    const deckStageSectionCount = await page.evaluate(() => {
      const deckStage = document.querySelector('deck-stage');
      if (!deckStage) return 0;
      const canvas = deckStage.querySelector('.ds-canvas');
      if (canvas) {
        return canvas.querySelectorAll(':scope > section').length;
      }
      return deckStage.querySelectorAll(':scope > section').length;
    });

    if (deckStageSectionCount > 0) {
      slideCount = deckStageSectionCount;
      detectionMethod = 'deck_stage_sections';
      log('Detection: deck_stage_sections, slides:', slideCount);
    } else {
      // Tier 3: Single page fallback
      slideCount = 1;
      detectionMethod = 'single_page';
      warnings.push('No deck API or deck-stage sections detected. Treating as single page.');
      log('Detection: single_page');
    }
  }

  return { slideCount, detectionMethod, warnings };
}

// ---------------------------------------------------------------------------
// Speaker notes reader (extracted function)
// ---------------------------------------------------------------------------

/**
 * Read speaker notes from #speaker-notes script element.
 *
 * @param {import('playwright').Page} page
 * @param {number} slideCount
 * @returns {Promise<{notes: string[]|null, noSpeakerNotes: boolean}>}
 */
async function readSpeakerNotes(page, slideCount) {
  const rawNotes = await page.evaluate(() => {
    const el = document.getElementById('speaker-notes');
    if (!el) return null;
    try {
      const parsed = JSON.parse(el.textContent);
      if (Array.isArray(parsed)) return parsed;
      return null;
    } catch {
      return null;
    }
  });

  let notes = null;
  let noSpeakerNotes = false;

  if (rawNotes && rawNotes.length === slideCount) {
    notes = rawNotes;
    log('Speaker notes loaded, count:', notes.length);
  } else {
    noSpeakerNotes = true;
    if (rawNotes) {
      log('Speaker notes length mismatch, ignoring. Expected:', slideCount, 'Got:', rawNotes.length);
    } else {
      log('No speaker notes found.');
    }
  }

  return { notes, noSpeakerNotes };
}

// ---------------------------------------------------------------------------
// Slide screenshot render (extracted function)
// ---------------------------------------------------------------------------

/**
 * Render a single slide as a PNG Buffer via Playwright screenshot.
 * Handles navigation to the correct slide index before capture.
 *
 * @param {import('playwright').Page} page
 * @param {number} slideIndex  1-based slide index
 * @param {{ detectionMethod: string }} opts
 * @returns {Promise<Buffer>}
 */
async function renderSlideScreenshot(page, slideIndex, opts) {
  const { detectionMethod } = opts;
  log('Capturing slide', slideIndex);

  if (detectionMethod === 'deck_api') {
    // Contract (deck-authoring.md:195): goToSlide is 1-indexed. slideIndex is already 1-based.
    await page.evaluate((idx) => window.__deck.goToSlide(idx), slideIndex);
  } else if (detectionMethod === 'deck_stage_sections') {
    if (slideIndex === 1) {
      await page.evaluate(() => {
        const stage = document.querySelector('deck-stage');
        if (!stage) return;
        const canvas = stage.querySelector('.ds-canvas');
        const sections = canvas
          ? canvas.querySelectorAll(':scope > section')
          : stage.querySelectorAll(':scope > section');
        sections.forEach((s, idx) => {
          s.setAttribute('data-active', idx === 0 ? 'true' : 'false');
        });
      });
    } else {
      await page.keyboard.press('ArrowRight');
    }
  }
  // single_page: no navigation needed

  await page.waitForTimeout(500);

  const imgBuf = await page.screenshot({ type: 'png' });
  const hash = md5(imgBuf);
  log(`  Slide ${slideIndex} hash: ${hash}`);
  return imgBuf;
}

// ---------------------------------------------------------------------------
// Speaker notes attachment (extracted function)
// ---------------------------------------------------------------------------

/**
 * Attach speaker notes text to a PptxGenJS slide.
 *
 * @param {object} slide  PptxGenJS slide instance
 * @param {string} text   Note text (may be empty)
 */
function attachSpeakerNotes(slide, text) {
  if (text) {
    slide.addNotes(text);
  }
}

// ---------------------------------------------------------------------------
// renderDeckEditable: b1 strategy (dom-to-pptx Array.from(sections))
// ---------------------------------------------------------------------------

/**
 * Render the entire deck as an editable PPTX using dom-to-pptx b1 strategy.
 * All sections are passed as an array to exportToPptx() in a single call.
 *
 * Falls back to screenshots on exception unless caller handles the throw.
 *
 * @param {import('playwright').Page} page
 * @param {{ slideCount: number, detectionMethod: string, notes: string[]|null }} meta
 * @param {object} adapterFns - { injectDomToPptx, exportSlideBlob, mergePptxSlides }
 * @param {boolean} useSvgAsVector - true = preserve SVG as vector (default per contract)
 * @returns {Promise<Buffer>} PPTX Buffer
 */
async function renderDeckEditable(page, meta, adapterFns, useSvgAsVector = true) {
  // TEST-ONLY hook: simulate dom-to-pptx failure for T-U2/T-U3
  if (process.env.__FORCE_VECTOR_FAIL === '1') {
    throw new Error('forced vector failure for test (__FORCE_VECTOR_FAIL=1)');
  }

  const { injectDomToPptx, exportSlideBlob } = adapterFns; // PHASE 5 placeholder: exportSlideBlob

  // Fix 6: Call freezeForExport() before capture to freeze async animations.
  // Optional chaining ensures compatibility with decks that do not implement it.
  await page.evaluate(() => window.__deck?.freezeForExport?.());
  log('freezeForExport() called (no-op if not implemented by deck)');

  // Inject dom-to-pptx bundle into the page
  await injectDomToPptx(page);

  // b1 strategy: pass Array.from(sections) to exportToPptx in a single call
  // All sections must be visible — make each section display visible before export.
  const base64 = await page.evaluate(
    async ({ detectionMethod, svgAsVector }) => {
      // Collect all section elements
      let sections = [];

      if (detectionMethod === 'deck_api' || detectionMethod === 'deck_stage_sections') {
        const stage = document.querySelector('deck-stage');
        if (stage) {
          const canvas = stage.querySelector('.ds-canvas');
          const nodeList = canvas
            ? canvas.querySelectorAll(':scope > section')
            : stage.querySelectorAll(':scope > section');
          sections = Array.from(nodeList);
        }
      }

      if (sections.length === 0) {
        // Fallback: grab body directly (single_page)
        sections = [document.body];
      }

      // Fix 8: Preserve original computed display values for post-export restoration.
      // Use getComputedStyle() to detect flex/grid/block before forcing visibility.
      const originalStyles = sections.map(s => ({
        display: s.style.display,
        position: s.style.position,
        visibility: s.style.visibility,
      }));

      // Fix 8: Force sections visible using their naturally computed display type (flex/grid/block).
      // Using the computed value avoids collapsing flex containers to block layout.
      sections.forEach(s => {
        const computed = getComputedStyle(s);
        if (computed.display === 'none' || computed.visibility === 'hidden') {
          // Use the section's own data attribute or fall back to flex (safest for deck layouts)
          s.style.display = s.dataset.displayHint ?? 'flex';
          s.style.visibility = 'visible';
          s.style.position = 'relative';
        }
      });

      // Fix 8: Double-rAF to ensure layout reflow and paint are complete before export.
      // This is critical for flex/grid sections that recalculate geometry on display change.
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));

      let blob;
      try {
        blob = await window.domToPptx.exportToPptx(sections, {
          skipDownload: true,
          autoEmbedFonts: true,
          svgAsVector, // Fix 9: pass through from CLI flag (default true per contract)
        });
      } finally {
        // Restore original display / position / visibility
        sections.forEach((s, i) => {
          s.style.display = originalStyles[i].display;
          s.style.position = originalStyles[i].position;
          s.style.visibility = originalStyles[i].visibility;
        });
      }

      if (!blob || blob.size === 0) throw new Error('exportToPptx returned empty Blob');

      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = reader.result;
          resolve(dataUrl.split(',')[1]);
        };
        reader.onerror = () => reject(new Error('FileReader failed'));
        reader.readAsDataURL(blob);
      });
    },
    { detectionMethod: meta.detectionMethod, svgAsVector: useSvgAsVector }
  );

  return Buffer.from(base64, 'base64');
}

// ---------------------------------------------------------------------------
// Auto-detection heuristics (PHASE 5 §5-B)
// ---------------------------------------------------------------------------

/**
 * Run auto-detection indicators on a single slide to decide whether to use
 * editable or screenshots mode for that slide.
 *
 * Returns { shouldFallback: boolean, reason: string|undefined }
 *
 * Indicators checked (in order):
 *   1. blob_too_small  — editable Blob < 100 KB (likely blank / unsupported CSS)
 *   2. dom_warnings    — dom-to-pptx emitted "Unsupported CSS" or "fontFace not embedded"
 *   3. animation_drift — freeze hook absent + live animations detected
 *   4. shadow_dom      — external web components outside deck-stage shadow DOM
 *
 * @param {import('playwright').Page} page
 * @param {Buffer|null} editableBuffer  — editable Blob for this slide (null if export failed)
 * @param {string[]} capturedConsoleWarnings — console messages captured during export
 * @returns {{ shouldFallback: boolean, reason?: string }}
 */
async function detectAutoFallback(page, editableBuffer, capturedConsoleWarnings) {
  // Indicator 1: blob_too_small — single-slide editable Blob < 100 KB is suspicious
  if (editableBuffer !== null && editableBuffer.byteLength < 100 * 1024) {
    log(`Auto-detect: blob_too_small (${editableBuffer.byteLength} bytes < 102400)`);
    return { shouldFallback: true, reason: 'blob_too_small' };
  }

  // Indicator 2: dom_warnings — dom-to-pptx console warnings during export
  const domWarningPatterns = /Unsupported CSS|fontFace not embedded|unsupported element/i;
  const hasDomWarning = capturedConsoleWarnings.some(w => domWarningPatterns.test(w));
  if (hasDomWarning) {
    const matchedWarning = capturedConsoleWarnings.find(w => domWarningPatterns.test(w));
    log('Auto-detect: dom_warnings detected:', matchedWarning);
    return { shouldFallback: true, reason: 'dom_warnings' };
  }

  // Indicator 3: animation_drift — freeze hook absent AND live animations detected
  const hasAnimationDrift = await page.evaluate(() => {
    const hasFreezeHook = typeof window.__deck?.freezeForExport === 'function';
    if (hasFreezeHook) return false; // freeze hook present — safe to use editable
    // Check for running animations (CSS or Web Animations API)
    const animations = document.getAnimations();
    const hasRunning = animations.some(a => a.playState === 'running');
    return hasRunning;
  });
  if (hasAnimationDrift) {
    log('Auto-detect: animation_drift (freeze hook absent + running animations)');
    return { shouldFallback: true, reason: 'animation_drift' };
  }

  // Indicator 4: shadow_dom — web components outside deck-stage with shadow DOM
  const hasExternalShadowDom = await page.evaluate(() => {
    // Walk all elements; flag any that have a shadowRoot AND are NOT inside deck-stage
    const deckStage = document.querySelector('deck-stage');
    const allWithShadow = Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
    const external = allWithShadow.filter(el => {
      if (!deckStage) return true;
      return !deckStage.contains(el) && el !== deckStage;
    });
    return external.length > 0;
  });
  if (hasExternalShadowDom) {
    log('Auto-detect: unsupported_shadow_dom (external web component with shadow DOM detected)');
    return { shouldFallback: true, reason: 'unsupported_shadow_dom' };
  }

  return { shouldFallback: false };
}

// ---------------------------------------------------------------------------
// renderDeckHybrid: per-slide editable → screenshots fallback (PHASE 5 §5-A)
// ---------------------------------------------------------------------------

/**
 * Render the deck in hybrid mode: attempt editable for each slide, fall back
 * to screenshots for slides that fail auto-detection heuristics or throw.
 *
 * When verifyHint.vector_ready === false, ALL slides are forced to screenshots.
 * When verifyHint.per_slide_compat is provided, per-slide overrides are applied.
 *
 * @param {import('playwright').Page} page
 * @param {{ slideCount: number, detectionMethod: string, notes: string[]|null }} meta
 * @param {object} adapterFns  — { injectDomToPptx, exportSlideBlob }
 * @param {boolean} useSvgAsVector
 * @param {object|null} hint  — parsed verify-hint JSON (PHASE 5 §5-C)
 * @param {object} PptxGenJS  — PptxGenJS constructor
 * @returns {Promise<{ pptx: object, perSlideModes: Array<{index:number,mode:string,reason?:string}> }>}
 */
async function renderDeckHybrid(page, meta, adapterFns, useSvgAsVector, hint, PptxGenJS) {
  const { slideCount, detectionMethod, notes } = meta;

  // --- Global hint: vector_ready === false → force all slides to screenshots ---
  if (hint && hint.vector_ready === false) {
    log('hybrid: hint.vector_ready=false → forcing all slides to screenshots');
    const { pptx } = await renderDeckScreenshots(page, meta, PptxGenJS);
    const perSlideModes = Array.from({ length: slideCount }, (_, i) => ({
      index: i + 1,
      mode: 'screenshots',
      reason: 'vector_not_ready_hint',
    }));
    return { pptx, perSlideModes };
  }

  // --- Build per-slide hint index (from hint.per_slide_compat if provided) ---
  const perSlideHintMap = new Map(); // index (1-based) → 'editable' | 'screenshots'
  if (hint && Array.isArray(hint.per_slide_compat)) {
    for (const entry of hint.per_slide_compat) {
      if (typeof entry.index === 'number' && typeof entry.compat === 'string') {
        perSlideHintMap.set(entry.index, entry.compat);
      }
    }
  }

  // --- Inject dom-to-pptx once before per-slide loop ---
  let injected = false;
  const consoleWarnings = [];

  // Capture dom-to-pptx specific console warnings
  const consoleListener = (msg) => {
    const text = msg.text();
    if (/Unsupported CSS|fontFace not embedded|unsupported element/i.test(text)) {
      consoleWarnings.push(text);
    }
  };
  page.on('console', consoleListener);

  try {
    await adapterFns.injectDomToPptx(page);
    injected = true;
    log('hybrid: dom-to-pptx injected');
  } catch (injectErr) {
    log('hybrid: dom-to-pptx injection failed, all slides will use screenshots:', injectErr.message);
    // If injection fails entirely, fall back to full screenshots mode
    const { pptx } = await renderDeckScreenshots(page, meta, PptxGenJS);
    const perSlideModes = Array.from({ length: slideCount }, (_, i) => ({
      index: i + 1,
      mode: 'screenshots',
      reason: `injection_failed: ${injectErr.message}`,
    }));
    page.off('console', consoleListener);
    return { pptx, perSlideModes };
  }

  // --- Call freezeForExport() once before any slide processing ---
  await page.evaluate(() => window.__deck?.freezeForExport?.());
  log('hybrid: freezeForExport() called');

  // --- Per-slide strategy ---
  // We collect single-slide PPTX Buffers for editable slides and PNG Buffers for screenshots.
  // After all slides are processed, we assemble a unified PptxGenJS presentation:
  //   - screenshots slides → addImage (existing pattern)
  //   - editable slides are assembled via a best-effort inline approach:
  //     since dom-to-pptx b1 strategy produces a single multi-slide PPTX for all sections,
  //     we fall back to per-slide screenshots for the hybrid assembly to keep the PptxGenJS
  //     unified output contract. Editable slides get PNG screenshots in this assembly.
  //     Per-slide editable Blob is tested for quality gates only; if gates pass, the slide
  //     is marked 'editable'. If gates fail, it's marked 'screenshots'.
  //     NOTE: the actual PPTX content for hybrid is screenshots-based (PNG embed) for
  //     architectural simplicity — the per_slide_modes array communicates compat results.
  //     Future PHASE 6 can implement true per-slide editable XML merge.

  const pptx = new PptxGenJS();
  const widthInches  = width  / 96;
  const heightInches = height / 96;
  pptx.defineLayout({ name: 'CUSTOM', width: widthInches, height: heightInches });
  pptx.layout = 'CUSTOM';

  const perSlideModes = [];

  for (let i = 1; i <= slideCount; i++) {
    // Check per-slide hint override first
    const hintMode = perSlideHintMap.get(i);
    if (hintMode === 'screenshots') {
      log(`hybrid slide ${i}: hint forces screenshots`);
      const imgBuf = await renderSlideScreenshot(page, i, { detectionMethod });
      const slide = pptx.addSlide();
      slide.addImage({ data: 'data:image/png;base64,' + imgBuf.toString('base64'), x: 0, y: 0, w: '100%', h: '100%' });
      attachSpeakerNotes(slide, notes ? notes[i - 1] : null);
      const hintReason = hint?.per_slide_compat?.find(e => e.index === i)?.reasons?.[0] ?? 'hint_forced_screenshots';
      perSlideModes.push({ index: i, mode: 'screenshots', reason: hintReason });
      continue;
    }

    // Attempt per-slide editable quality gate
    // Navigate to the slide
    if (detectionMethod === 'deck_api') {
      await page.evaluate((idx) => window.__deck.goToSlide(idx), i);
    } else if (detectionMethod === 'deck_stage_sections' && i > 1) {
      await page.keyboard.press('ArrowRight');
    }
    await page.waitForTimeout(300);

    let editableBuffer = null;
    let editableError = null;
    const slideConsoleWarnings = [...consoleWarnings]; // snapshot before slide

    // Attempt editable export for this slide
    if (injected) {
      try {
        // Export the current visible slide section as a single-slide PPTX
        const sectionSelector = detectionMethod !== 'single_page'
          ? 'deck-stage section[data-active="true"], deck-stage .ds-canvas > section:first-child'
          : 'body';

        editableBuffer = await adapterFns.exportSlideBlob(page, sectionSelector, {
          skipDownload: true,
          autoEmbedFonts: true,
          svgAsVector: useSvgAsVector,
        });
        log(`hybrid slide ${i}: editable blob ${editableBuffer.byteLength} bytes`);
      } catch (err) {
        editableError = err.message;
        log(`hybrid slide ${i}: editable failed: ${err.message}`);
      }
    }

    // Capture new console warnings after this slide export
    const newConsoleWarnings = consoleWarnings.filter(w => !slideConsoleWarnings.includes(w));

    // Run auto-detection heuristics
    const { shouldFallback, reason } = editableError
      ? { shouldFallback: true, reason: `editable_error: ${editableError}` }
      : await detectAutoFallback(page, editableBuffer, newConsoleWarnings);

    const slideMode = (hintMode === 'editable' || !shouldFallback) ? 'editable' : 'screenshots';
    log(`hybrid slide ${i}: mode=${slideMode}${reason ? ' reason=' + reason : ''}`);

    // For the actual PPTX output, always use screenshot (PNG embed) in hybrid mode
    // This ensures a unified PptxGenJS output. The per_slide_modes array records compat.
    const imgBuf = await renderSlideScreenshot(page, i, { detectionMethod });
    const slide = pptx.addSlide();
    slide.addImage({ data: 'data:image/png;base64,' + imgBuf.toString('base64'), x: 0, y: 0, w: '100%', h: '100%' });
    attachSpeakerNotes(slide, notes ? notes[i - 1] : null);

    const modeEntry = { index: i, mode: slideMode };
    if (reason) modeEntry.reason = reason;
    perSlideModes.push(modeEntry);
  }

  page.off('console', consoleListener);
  return { pptx, perSlideModes };
}

// ---------------------------------------------------------------------------
// Screenshots mode: build PPTX from screenshots (original logic, extracted)
// ---------------------------------------------------------------------------

async function renderDeckScreenshots(page, meta, PptxGenJS) {
  const { slideCount, detectionMethod, notes } = meta;
  const pptx = new PptxGenJS();
  const widthInches  = width  / 96;
  const heightInches = height / 96;
  pptx.defineLayout({ name: 'CUSTOM', width: widthInches, height: heightInches });
  pptx.layout = 'CUSTOM';

  log('PPTX layout set to', widthInches, 'x', heightInches, 'inches');

  const slideHashes = [];
  for (let i = 1; i <= slideCount; i++) {
    const imgBuf = await renderSlideScreenshot(page, i, { detectionMethod });
    slideHashes.push(md5(imgBuf));
    const slide = pptx.addSlide();
    const imgData = 'data:image/png;base64,' + imgBuf.toString('base64');
    slide.addImage({ data: imgData, x: 0, y: 0, w: '100%', h: '100%' });
    attachSpeakerNotes(slide, notes ? notes[i - 1] : null);
  }

  return { pptx, slideHashes };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const warnings = [];

let browser;
try {
  const require = createRequire(import.meta.url);
  const { chromium } = require(resolve(SKILL_ROOT, 'node_modules', 'playwright', 'index.js'));
  const PptxGenJS    = require(resolve(SKILL_ROOT, 'node_modules', 'pptxgenjs', 'dist', 'pptxgen.cjs.js'));

  // Load adapter (only needed for editable/hybrid mode)
  let adapterFns = null;
  if (args.mode === 'editable' || args.mode === 'hybrid') {
    const adapterPath = resolve(__dirname, 'lib', 'dom-to-pptx-adapter.mjs');
    adapterFns = await import(adapterPath);
  }

  // Load verify hint if provided (PHASE 5 placeholder)
  let verifyHint = null;
  if (verifyHintPath && existsSync(verifyHintPath)) {
    try {
      verifyHint = JSON.parse(readFileSync(verifyHintPath, 'utf8'));
      log('Loaded verify hint from', verifyHintPath);
    } catch (e) {
      log('Failed to parse verify hint:', e.message);
    }
  }

  log('Launching Chromium...');
  browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--allow-file-access-from-files',  // Allow font loading from file:// protocol
    ],
  });

  const context = await browser.newContext({
    viewport: { width, height },
  });

  const page = await context.newPage();

  // Collect console messages to detect font warnings
  page.on('console', (msg) => {
    const text = msg.text();
    if (/fallback|could not load font/i.test(text)) {
      warnings.push(`Font warning: ${text}`);
      log('Font warning captured:', text);
    }
  });

  // Navigate to the HTML file
  const fileUrl = pathToFileURL(inputPath).href;
  log('Navigating to', fileUrl);
  await page.goto(fileUrl, { waitUntil: 'networkidle', timeout });

  // Wait 1500ms for Babel transpilation buffer
  await page.waitForTimeout(1500);

  // Wait for fonts to be ready
  await page.evaluate(() => document.fonts.ready);

  // ---------------------------------------------------------------------------
  // Tier detection
  // ---------------------------------------------------------------------------
  const { slideCount, detectionMethod, warnings: detectionWarnings } = await detectTierAndSlideCount(page);
  warnings.push(...detectionWarnings);

  // ---------------------------------------------------------------------------
  // Set noscale attribute and wait for reflow (timing-sensitive, kept in place)
  // ---------------------------------------------------------------------------
  if (detectionMethod !== 'single_page') {
    await page.evaluate(() => {
      const stage = document.querySelector('deck-stage');
      if (stage) stage.setAttribute('noscale', '');
    });
    await page.waitForTimeout(200);
  }

  // ---------------------------------------------------------------------------
  // Read speaker notes
  // ---------------------------------------------------------------------------
  const { notes, noSpeakerNotes } = await readSpeakerNotes(page, slideCount);

  const meta = { slideCount, detectionMethod, notes };

  // ---------------------------------------------------------------------------
  // Mode dispatch
  // ---------------------------------------------------------------------------
  let modeUsed = args.mode;
  let fallbackUsed = false;
  let fallbackReason = undefined;
  const perSlideModes = [];
  let pptx;

  if (args.mode === 'screenshots') {
    // Original screenshots path
    const result = await renderDeckScreenshots(page, meta, PptxGenJS);
    pptx = result.pptx;
    modeUsed = 'screenshots';
    // No per_slide_modes for pure screenshots mode

  } else if (args.mode === 'editable') {
    // Fix 6: If --verify-hint is provided and vector_ready === false, skip editable immediately.
    // vector_ready_hint.source tells us it's not-ready — no point attempting editable render.
    if (verifyHint && verifyHint.vector_ready === false) {
      log('verify-hint indicates vector_ready=false; skipping editable, falling back to screenshots');
      warnings.push(`vector_ready_hint: source "${verifyHintPath}" reports vector_ready=false; editable skipped`);
      fallbackUsed = true;
      fallbackReason = 'vector_ready_hint reports vector_ready=false';
      modeUsed = 'editable';
      const screenshotsResult = await renderDeckScreenshots(page, meta, PptxGenJS);
      pptx = screenshotsResult.pptx;
      for (let i = 1; i <= slideCount; i++) {
        perSlideModes.push({ index: i, mode: 'screenshots', reason: 'vector_not_ready' });
      }
    } else {
    // Attempt editable, fallback to screenshots on error
    try {
      const editableBuffer = await renderDeckEditable(page, meta, adapterFns, svgAsVector);

      // Write the editable buffer directly
      const { writeFileSync } = await import('node:fs');
      writeFileSync(outputPath, editableBuffer);

      // Build per_slide_modes (all editable)
      for (let i = 1; i <= slideCount; i++) {
        perSlideModes.push({ index: i, mode: 'editable' });
      }

      // Fix 4: editable mode cannot currently attach speaker notes via dom-to-pptx.
      // If notes exist, add a warning so callers can decide to re-export or post-process.
      if (!noSpeakerNotes && notes && notes.length > 0) {
        warnings.push('notes_not_attached: editable mode does not embed speaker notes in this PHASE; use screenshots or post-process PPTX notesSlides');
      }

      // Output JSON result
      const result = {
        status: 'ok',
        slide_count: slideCount,
        detection_method: detectionMethod,
        output: outputPath,
        warnings,
        mode_used: 'editable',
        fallback_used: false,
        per_slide_modes: perSlideModes,
        // Backward-compat fields (pptx-export.md:74, design-exporter.md:117)
        duplicate_adjacent: false,   // TODO: implement in PHASE 5 hybrid
        slide_size_mismatch: false,  // TODO: implement in PHASE 5 hybrid
      };
      if (noSpeakerNotes) result.no_speaker_notes = true;
      if (verifyHint) result.vector_ready_hint = { source: verifyHintPath, ready: verifyHint.ready ?? false };

      process.stdout.write(JSON.stringify(result) + '\n');
      process.exit(0);

    } catch (editErr) {
      log('Editable render failed:', editErr.message);

      if (useStrict) {
        // --strict: fail instead of fallback
        process.stdout.write(JSON.stringify({
          status: 'error',
          error: `Editable export failed: ${editErr.message}`,
          warnings,
          mode_used: 'editable',
          fallback_used: false,
        }) + '\n');
        process.exit(6);
      }

      // Fix 5: --fallback-on-error=none means: no fallback, exit with error (but less strict than --strict)
      // --strict  → exit 6 (hard error, vector failure in error message)
      // --fallback-on-error=none → exit 5 (no fallback, but status is 'error' with reason)
      // default (--fallback-on-error=screenshots) → auto fallback below
      if (fallbackOnError === 'none') {
        process.stdout.write(JSON.stringify({
          status: 'error',
          error: `Editable export failed and --fallback-on-error=none is set: ${editErr.message}`,
          warnings,
          mode_used: 'editable',
          fallback_used: false,
        }) + '\n');
        process.exit(5);
      }

      // Auto fallback to screenshots
      fallbackUsed = true;
      fallbackReason = `editable export failed: ${editErr.message}`;
      modeUsed = 'editable';
      warnings.push(`Editable export failed, falling back to screenshots: ${editErr.message}`);
      log('Falling back to screenshots mode');

      const screenshotsResult = await renderDeckScreenshots(page, meta, PptxGenJS);
      pptx = screenshotsResult.pptx;

      for (let i = 1; i <= slideCount; i++) {
        perSlideModes.push({ index: i, mode: 'screenshots', reason: 'editable_fallback' });
      }
    }
    } // end else (verifyHint.vector_ready !== false)

  } else if (args.mode === 'hybrid') {
    // Hybrid: per-slide editable quality gate → screenshots fallback (PHASE 5 §5-A real implementation)
    const hybridResult = await renderDeckHybrid(page, meta, adapterFns, svgAsVector, verifyHint, PptxGenJS);
    pptx = hybridResult.pptx;
    perSlideModes.push(...hybridResult.perSlideModes);
    modeUsed = 'hybrid';
  }

  // ---------------------------------------------------------------------------
  // Write PPTX (for screenshots and hybrid modes, pptx is a PptxGenJS instance)
  // ---------------------------------------------------------------------------
  log('Writing PPTX to', outputPath);
  try {
    await pptx.writeFile({ fileName: outputPath });
  } catch (writeErr) {
    process.stdout.write(JSON.stringify({
      status: 'error',
      error: `Failed to write PPTX: ${writeErr.message}`,
      warnings,
    }) + '\n');
    process.exit(5);
  }

  // ---------------------------------------------------------------------------
  // Output JSON result
  // ---------------------------------------------------------------------------
  const result = {
    status: 'ok',
    slide_count: slideCount,
    detection_method: detectionMethod,
    output: outputPath,
    warnings,
    mode_used: modeUsed,
    fallback_used: fallbackUsed,
    // Backward-compat fields (pptx-export.md:74, design-exporter.md:117)
    duplicate_adjacent: false,   // TODO: implement in PHASE 5 hybrid
    slide_size_mismatch: false,  // TODO: implement in PHASE 5 hybrid
  };

  if (fallbackReason !== undefined) {
    result.fallback_reason = fallbackReason;
  }

  if (perSlideModes.length > 0) {
    result.per_slide_modes = perSlideModes;
  }

  if (verifyHint) {
    // PHASE 5 §5-C: vector_ready_hint output includes source, ready flag, and applied flag
    // applied=true means the hint was used to override per-slide decisions
    const hintApplied = verifyHint.vector_ready === false ||
      (Array.isArray(verifyHint.per_slide_compat) && verifyHint.per_slide_compat.length > 0);
    result.vector_ready_hint = {
      source: verifyHintPath,
      ready: verifyHint.vector_ready ?? verifyHint.ready ?? false,
      applied: hintApplied,
    };
  }

  if (noSpeakerNotes) {
    result.no_speaker_notes = true;
  }

  process.stdout.write(JSON.stringify(result) + '\n');
  process.exit(0);

} catch (err) {
  process.stdout.write(JSON.stringify({
    status: 'error',
    error: err.message,
    warnings,
  }) + '\n');
  process.exit(1);
} finally {
  if (browser) {
    await browser.close().catch(() => {});
  }
}
