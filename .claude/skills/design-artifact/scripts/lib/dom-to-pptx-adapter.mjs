/**
 * dom-to-pptx-adapter.mjs
 *
 * Adapter layer between Playwright page context and dom-to-pptx library.
 * Handles local script injection, slide Blob extraction, and multi-slide
 * PPTX assembly via JSZip rel-id renumbering (strategy b2).
 *
 * Three exported functions:
 *   injectDomToPptx(page)
 *   exportSlideBlob(page, selector, options)
 *   mergePptxSlides(slideBuffers, notes, layout)
 */

import { fileURLToPath } from 'url';
import path from 'path';
import JSZip from 'jszip';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Resolve the local bundle path — never load from CDN
function getBundlePath() {
  try {
    // Try to resolve the bundle from the design-artifact package context
    const pkgDir = path.resolve(__dirname, '../../');
    return path.join(pkgDir, 'node_modules/dom-to-pptx/dist/dom-to-pptx.bundle.js');
  } catch (err) {
    throw new Error(`dom-to-pptx bundle not found. Run: npm i dom-to-pptx in design-artifact/. (${err.message})`);
  }
}

/**
 * Inject dom-to-pptx bundle into a Playwright page using the local file path.
 * Must be called after page.goto() and before any exportSlideBlob() calls.
 *
 * @param {import('playwright').Page} page - Playwright page instance
 * @returns {Promise<void>}
 */
export async function injectDomToPptx(page) {
  const bundlePath = getBundlePath();
  await page.addScriptTag({ path: bundlePath });

  // Verify the global was registered
  const ok = await page.evaluate(() => typeof window.domToPptx?.exportToPptx === 'function');
  if (!ok) {
    throw new Error('dom-to-pptx bundle injected but window.domToPptx.exportToPptx not found');
  }
}

/**
 * Export a single slide (or multiple elements) as a PPTX Blob, then return
 * it as a Node.js Buffer. Uses skipDownload:true to suppress the browser's
 * native save-as dialog.
 *
 * @param {import('playwright').Page} page - Playwright page instance (bundle already injected)
 * @param {string|string[]} selector - CSS selector string or array of selectors / elements
 * @param {object} [options] - dom-to-pptx options (svgAsVector, autoEmbedFonts, etc.)
 * @returns {Promise<Buffer>} Raw PPTX bytes
 */
export async function exportSlideBlob(page, selector, options = {}) {
  const base64 = await page.evaluate(
    async ({ selector, options }) => {
      // Support both string selector and array of selectors
      let target;
      if (Array.isArray(selector)) {
        target = selector.map(s => (typeof s === 'string' ? document.querySelector(s) : s)).filter(Boolean);
        if (target.length === 0) throw new Error('exportSlideBlob: no elements matched selectors array');
      } else {
        target = selector; // pass string directly — dom-to-pptx resolves it internally
      }

      const blob = await window.domToPptx.exportToPptx(target, {
        skipDownload: true,
        autoEmbedFonts: true,
        svgAsVector: false, // default off; caller can override via options
        ...options,
      });

      if (!blob || blob.size === 0) throw new Error('exportToPptx returned empty Blob');

      // Convert Blob to base64 inside the browser context
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = reader.result;
          // Strip the data:application/...;base64, prefix
          const base64Data = dataUrl.split(',')[1];
          resolve(base64Data);
        };
        reader.onerror = () => reject(new Error('FileReader failed'));
        reader.readAsDataURL(blob);
      });
    },
    { selector, options }
  );

  return Buffer.from(base64, 'base64');
}

/**
 * Merge multiple single-slide PPTX Buffers into one multi-slide PPTX Buffer.
 *
 * Strategy b2: Each dom-to-pptx call produces a valid single-slide PPTX
 * (slide1.xml + _rels/slide1.xml.rels + theme + fonts). We:
 *   1. Parse each PPTX with JSZip
 *   2. Extract slide XML + rels from each, renumbering to avoid collisions
 *   3. Merge theme/fonts from the first PPTX (dedup by filename)
 *   4. Rebuild [Content_Types].xml and presentation.xml slide list
 *   5. Attach speaker notes as notesSlide XML
 *
 * @param {Buffer[]} slideBuffers - Array of single-slide PPTX Buffers (one per slide)
 * @param {string[]} [notes] - Speaker note strings, one per slide (can be empty string)
 * @param {{ width?: number, height?: number }} [layout] - Slide dimensions in EMU (default 1920x1080 px → 6858000 x 3861000 EMU)
 * @returns {Promise<Buffer>} Merged PPTX Buffer
 */
export async function mergePptxSlides(slideBuffers, notes = [], layout = {}) {
  if (!slideBuffers || slideBuffers.length === 0) {
    throw new Error('mergePptxSlides: slideBuffers must be a non-empty array');
  }

  const slideCount = slideBuffers.length;
  // 1 px = 9144 EMU.  1920*9144 = 17538048, 1080*9144 = 9873720
  // dom-to-pptx default is likely 960x540 px unless width/height overridden.
  // We keep whatever the source PPTX uses unless caller passes layout.
  const cx = layout.width  ?? null; // null = keep from source
  const cy = layout.height ?? null;

  // Parse all source ZIPs
  const zips = await Promise.all(slideBuffers.map(buf => JSZip.loadAsync(buf)));

  // Output ZIP
  const outZip = new JSZip();

  // Collect merged data
  const addedFiles = new Set();
  const slideXmls = [];        // { xml, relsXml }
  const notesXmls = [];        // noteSlide XML string per slide
  let presentationXml = null;
  let contentTypesXml = null;
  let presRelsXml = null;

  // --- Step 1: extract slide XMLs from each source ---
  for (let i = 0; i < slideCount; i++) {
    const zip = zips[i];
    const slideNum = i + 1; // target slide number in output

    // Get slide1.xml (dom-to-pptx always produces slide1 in a single-slide PPTX)
    const slideXmlRaw = await zip.file('ppt/slides/slide1.xml')?.async('string');
    if (!slideXmlRaw) {
      throw new Error(`mergePptxSlides: slide ${slideNum} source has no ppt/slides/slide1.xml`);
    }
    const slideRelsRaw = await zip.file('ppt/slides/_rels/slide1.xml.rels')?.async('string');

    // Renumber rel IDs to avoid collisions: prefix rId with slideNum
    const renumberedRels = slideRelsRaw
      ? slideRelsRaw.replace(/Id="rId(\d+)"/g, (_, n) => `Id="s${slideNum}rId${n}"`)
                    .replace(/Id="rId(\d+)"/g, (_, n) => `Id="s${slideNum}rId${n}"`) // double pass for safety
      : makeDefaultSlideRels(slideNum);

    const renumberedSlide = slideXmlRaw
      .replace(/r:id="rId(\d+)"/g, (_, n) => `r:id="s${slideNum}rId${n}"`)
      .replace(/r:embed="rId(\d+)"/g, (_, n) => `r:embed="s${slideNum}rId${n}"`);

    slideXmls.push({ xml: renumberedSlide, relsXml: renumberedRels });

    // Copy shared resources from FIRST slide only (theme, fonts, media, slideLayout, slideMaster)
    if (i === 0) {
      const entries = Object.keys(zip.files);
      for (const entry of entries) {
        // Skip per-slide files — we handle them ourselves
        if (
          entry === 'ppt/slides/slide1.xml' ||
          entry === 'ppt/slides/_rels/slide1.xml.rels' ||
          entry === '[Content_Types].xml' ||
          entry === 'ppt/presentation.xml' ||
          entry === 'ppt/_rels/presentation.xml.rels' ||
          entry.startsWith('ppt/notesSl')
        ) continue;

        if (!addedFiles.has(entry)) {
          const content = await zip.file(entry)?.async('nodebuffer');
          if (content) {
            outZip.file(entry, content);
            addedFiles.add(entry);
          }
        }
      }

      // Cache presentation.xml and _rels for restructuring
      presentationXml = await zip.file('ppt/presentation.xml')?.async('string');
      presRelsXml     = await zip.file('ppt/_rels/presentation.xml.rels')?.async('string');
      contentTypesXml = await zip.file('[Content_Types].xml')?.async('string');
    }

    // Build notesSlide XML for this slide
    const noteText = (notes[i] || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    notesXmls.push(makeNotesSlideXml(slideNum, noteText));
  }

  // --- Step 2: add per-slide files to output ---
  for (let i = 0; i < slideCount; i++) {
    const n = i + 1;
    outZip.file(`ppt/slides/slide${n}.xml`, slideXmls[i].xml);
    outZip.file(`ppt/slides/_rels/slide${n}.xml.rels`, slideXmls[i].relsXml);
    outZip.file(`ppt/notesSlides/notesSlide${n}.xml`, notesXmls[i]);
    outZip.file(`ppt/notesSlides/_rels/notesSlide${n}.xml.rels`, makeNotesSlideRels(n));
  }

  // --- Step 3: rebuild presentation.xml with all slide references ---
  if (presentationXml) {
    const newPresXml = rebuildPresentationXml(presentationXml, slideCount, cx, cy);
    outZip.file('ppt/presentation.xml', newPresXml);
  }

  // --- Step 4: rebuild ppt/_rels/presentation.xml.rels ---
  if (presRelsXml) {
    const newPresRels = rebuildPresentationRels(presRelsXml, slideCount);
    outZip.file('ppt/_rels/presentation.xml.rels', newPresRels);
  }

  // --- Step 5: rebuild [Content_Types].xml ---
  if (contentTypesXml) {
    const newContentTypes = rebuildContentTypes(contentTypesXml, slideCount);
    outZip.file('[Content_Types].xml', newContentTypes);
  }

  // --- Step 6: generate output ---
  const outBuf = await outZip.generateAsync({
    type: 'nodebuffer',
    compression: 'DEFLATE',
    compressionOptions: { level: 6 },
  });

  return outBuf;
}

// ─── XML helpers ─────────────────────────────────────────────────────────────

function makeDefaultSlideRels(slideNum) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="s${slideNum}rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>`;
}

function makeNotesSlideXml(_slideNum, noteText) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
         xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
         xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree>
    <p:sp><p:nvSpPr>
      <p:cNvPr id="2" name="Notes Placeholder 1"/>
      <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
      <p:nvPr><p:ph type="body" idx="1"/></p:nvPr>
    </p:nvSpPr>
    <p:spPr/>
    <p:txBody>
      <a:bodyPr/>
      <a:lstStyle/>
      <a:p><a:r><a:t>${noteText}</a:t></a:r></a:p>
    </p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:notes>`;
}

function makeNotesSlideRels(slideNum) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide${slideNum}.xml"/>
</Relationships>`;
}

function rebuildPresentationXml(xml, slideCount, cx, cy) {
  // Replace the <p:sldIdLst> with entries for all slides
  const sldIdEntries = Array.from({ length: slideCount }, (_, i) => {
    const id = 256 + i; // standard starting id
    const rId = `rId${10 + i}`; // offset to avoid collision with theme/layout rels
    return `<p:sldId id="${id}" r:id="${rId}"/>`;
  }).join('\n    ');

  // Replace existing sldIdLst
  let out = xml.replace(/<p:sldIdLst>[\s\S]*?<\/p:sldIdLst>/, `<p:sldIdLst>\n    ${sldIdEntries}\n  </p:sldIdLst>`);

  // Update sldSz if layout provided
  if (cx && cy) {
    out = out.replace(/<p:sldSz[^/]*(\/?>)/, `<p:sldSz cx="${cx}" cy="${cy}" type="custom"$1`);
  }

  return out;
}

function rebuildPresentationRels(relsXml, slideCount) {
  // Remove existing slide relationships
  let out = relsXml.replace(/<Relationship[^>]+Type="[^"]*\/slide"[^/]*\/>/g, '');

  // Add new slide relationships
  const newRels = Array.from({ length: slideCount }, (_, i) => {
    const rId = `rId${10 + i}`;
    return `<Relationship Id="${rId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${i + 1}.xml"/>`;
  }).join('\n  ');

  out = out.replace('</Relationships>', `  ${newRels}\n</Relationships>`);
  return out;
}

function rebuildContentTypes(xml, slideCount) {
  // Remove existing slide/notesSlide overrides
  let out = xml
    .replace(/<Override[^>]+PartName="\/ppt\/slides\/slide\d+\.xml"[^/]*\/>/g, '')
    .replace(/<Override[^>]+PartName="\/ppt\/notesSlides\/notesSlide\d+\.xml"[^/]*\/>/g, '');

  const slideOverrides = Array.from({ length: slideCount }, (_, i) => {
    const n = i + 1;
    return [
      `<Override PartName="/ppt/slides/slide${n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`,
      `<Override PartName="/ppt/notesSlides/notesSlide${n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>`,
    ].join('\n  ');
  }).join('\n  ');

  // Ensure notesSlide Default exists
  if (!out.includes('notesSlide+xml')) {
    // Insert before closing tag
    out = out.replace('</Types>', `  <Default Extension="xml" ContentType="application/xml"/>\n</Types>`);
  }

  out = out.replace('</Types>', `  ${slideOverrides}\n</Types>`);
  return out;
}
