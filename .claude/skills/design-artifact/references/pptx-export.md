# PPTX Export Reference

> Reference for `scripts/export-pptx.mjs` — headless HTML-to-PPTX pipeline.

---

## 1. Purpose

`export-pptx.mjs` converts an HTML slide deck into a `.pptx` file by:

1. Launching headless Chromium via Playwright at a configurable viewport (default 1920x1080).
2. Navigating to the input HTML file using a `file://` URL.
3. Detecting slide boundaries via a 3-tier fallback (see Section 5).
4. Capturing a full-page PNG screenshot per slide using `page.screenshot()`.
5. Assembling slides into a PPTX using `pptxgenjs`, embedding screenshots as full-bleed images and speaker notes where available.
6. Writing the output file and printing a JSON result object to stdout.

The script is **opt-in only** — it is never called automatically. Callers invoke it explicitly via CLI or from within the `design-artifact` skill when the user passes `--export pptx`.

Call path: user request → `design-artifact` SKILL → `design-executor` subagent (or direct CLI) → `node scripts/export-pptx.mjs`.

---

## 2. Usage

Run from the project root or any directory. The script resolves all paths to absolute before use.

**Basic (default 1920x1080, output alongside input):**

```bash
node .claude/skills/design-artifact/scripts/export-pptx.mjs \
  --input designs/my-deck/index.html
```

**Explicit 1920x1080 viewport and named output:**

```bash
node .claude/skills/design-artifact/scripts/export-pptx.mjs \
  --input designs/my-deck/index.html \
  --output /tmp/my-deck.pptx \
  --width 1920 \
  --height 1080
```

**Calling `--mode editable` (unsupported — produces an error):**

```bash
node .claude/skills/design-artifact/scripts/export-pptx.mjs \
  --input designs/my-deck/index.html \
  --mode editable
# stdout: {"status":"error","error":"Unsupported mode: \"editable\". Only \"screenshots\" is supported."}
# exit code: 2
```

All options:

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--input` | `-i` | (required) | Path to input HTML file |
| `--output` | `-o` | `<input>.pptx` | Path to output PPTX file |
| `--mode` | | `screenshots` | Export mode; only `screenshots` is supported |
| `--width` | | `1920` | Playwright viewport width in pixels |
| `--height` | | `1080` | Playwright viewport height in pixels |
| `--timeout` | | `60000` | Page navigation timeout in milliseconds |
| `--verbose` | `-v` | `false` | Write debug lines to stderr |
| `--help` | `-h` | | Print usage and exit 0 |

---

## 3. Validation Flags

On success the script prints a single JSON line to stdout. The shape is:

```json
{
  "status": "ok",
  "slide_count": 5,
  "detection_method": "deck_api",
  "output": "/abs/path/to/deck.pptx",
  "no_speaker_notes": true,
  "duplicate_adjacent": true,
  "slide_size_mismatch": false,
  "warnings": ["Font warning: Could not load font 'NotoSansCJK-KR'"]
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `status` | `"ok"` \| `"error"` | `"ok"` means the PPTX was written successfully. `"error"` means the script aborted; `error` key will also be present. |
| `slide_count` | number | Number of slides captured and written to the PPTX. `0` indicates detection failed entirely. |
| `detection_method` | `"deck_api"` \| `"deck_stage_sections"` \| `"single_page"` | Which tier of slide detection was used (see Section 5). |
| `duplicate_adjacent` | boolean | `true` when two or more consecutive slides produced identical PNG hashes. Indicates that slide navigation did not advance — the same frame was captured twice. Most commonly caused by tier-2 `ArrowRight` timing instability. Absent (`undefined`) when `false`. |
| `slide_size_mismatch` | boolean | `true` when `--width` or `--height` were set to values other than 1920x1080. The PPTX layout will differ from the standard 16:9 deck ratio. Absent (`undefined`) when `false`. |
| `no_speaker_notes` | boolean | `true` when the deck's `#speaker-notes` JSON array was missing or its length did not match `slide_count`. PPTX is still created; notes are simply omitted. Absent (`undefined`) when notes were successfully embedded. |
| `warnings[]` | string array | Non-fatal observations collected during the run. Always present (may be empty). Typical entries: font fallback messages from Chromium, single-page detection notice. Does not cause a non-zero exit code. |

---

## 4. Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success — PPTX written, JSON result on stdout. |
| `1` | Unexpected runtime error (Playwright crash, unhandled exception). |
| `2` | Unsupported `--mode` value. Only `"screenshots"` is accepted. |
| `3` | Input file not found at the resolved path. |
| `4` | `--input` flag was not provided. |
| `5` | Output file write failure (disk full, permission denied, etc.). |

All non-zero exits also print a JSON error object to stdout: `{"status":"error","error":"<message>","warnings":[...]}`.

---

## 5. Slide Detection: 3-Tier Fallback

The script must determine how many slides exist and how to advance between them. It tries three strategies in order, stopping at the first that succeeds.

### Tier 1 — `deck_api` (preferred)

**When used:** The HTML page exposes a `window.__deck` object with both `getSlideCount()` and `goToSlide()` methods (see [deck-authoring.md — PPTX Export Contract](deck-authoring.md#pptx-export-contract-deck-stage--export-pptxmjs)).

**Requirements:** `window.__deck.getSlideCount()` returns a positive integer; `window.__deck.goToSlide(index)` accepts 1-indexed slide numbers, causes synchronous DOM updates, and treats out-of-range calls as no-ops.

**Behaviour:** The script calls `getSlideCount()` once, then iterates `goToSlide(i)` for `i = 1..N` and captures a screenshot after each call. Navigation is deterministic and fast because no timing heuristics are needed.

### Tier 2 — `deck_stage_sections` (legacy fallback)

**When used:** No `window.__deck` API was found, but a `<deck-stage>` element exists in the DOM with direct `<section>` children (inside `.ds-canvas` if present).

**Requirements:** The `<deck-stage>` web component must render its slides as `<section>` elements that are direct children of `.ds-canvas` (or of `deck-stage` itself). The component must respond to keyboard `ArrowRight` events by advancing to the next slide and updating the DOM synchronously within ~500 ms.

**Behaviour:** The script reads `section` count from the DOM. For slide 1 it directly sets `data-active` attributes to force the first slide active. For slides 2..N it dispatches `ArrowRight` keyboard events and waits 500 ms between captures. This approach is timing-dependent, which is why `duplicate_adjacent` detection exists to catch cases where the delay was insufficient.

### Tier 3 — `single_page` (last resort)

**When used:** Neither `window.__deck` nor `<deck-stage>` sections were detected.

**Requirements:** None — this path always succeeds.

**Behaviour:** `slide_count` is set to `1` and a single full-page screenshot is taken. A warning is added to `warnings[]`. The resulting PPTX contains exactly one slide. This is appropriate for non-deck HTML artifacts (prototypes, landing pages) that happen to be exported via this script.

---

## 6. Korean Font Notes

Playwright uses the Chromium binary bundled with the `playwright` npm package. Chromium relies on **system fonts** for rendering; it does not embed fonts from the HTML file's `@font-face` declarations unless the font file is locally available.

### macOS

`AppleSDGothicNeo` (Apple SD Gothic Neo) is available by default on macOS 10.10+ and is the standard Korean system font. Decks that specify `font-family: 'Apple SD Gothic Neo', sans-serif` render correctly without additional setup.

### Linux (CI environments)

Chromium on Linux has no Korean fonts installed by default. Before running the export script on a Linux host, install the Noto CJK font package:

```bash
# Debian / Ubuntu
apt-get install -y fonts-noto-cjk

# Fedora / RHEL
dnf install -y google-noto-sans-cjk-fonts
```

The font family name after installation is `NotoSansCJK-KR` (or `Noto Sans CJK KR`). Update your deck's CSS accordingly:

```css
font-family: 'Apple SD Gothic Neo', 'Noto Sans CJK KR', sans-serif;
```

### Font warning detection

During page load, Chromium emits console messages containing `"Could not load font"` or `"fallback"` when a requested font is unavailable. The script captures all `page.on('console')` events and adds matching messages to `warnings[]`. This is intentionally non-fatal — the PPTX is still produced, but affected text may render in a fallback sans-serif. On Linux CI, inspect `warnings[]` to confirm whether Korean fonts are rendering correctly before distributing the PPTX.

---

## 7. Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Playwright launch fails with `Error: Failed to launch browser` | Chromium binary is not installed in the skill's local `node_modules` | Run `bash .claude/skills/design-artifact/scripts/setup.sh` to reinstall dependencies |
| `Error: Executable doesn't exist at ...` | `playwright install` was never run for the local binary | Run `npx playwright install chromium` from `.claude/skills/design-artifact/` |
| `slide_count: 0` in output | The deck exposes neither `window.__deck` nor `<deck-stage>` sections; tier-3 still returns `slide_count: 1`, so `0` should not appear in normal operation — if it does, the deck HTML failed to load | Re-delegate to `design-executor` to add the `window.__deck` API to the deck |
| `duplicate_adjacent: true` | Tier-2 `ArrowRight` navigation timing was too fast; adjacent screenshots captured the same frame | Add `window.__deck` API to the deck (deck-authoring.md Section 1) to use deterministic tier-1 navigation |
| Korean text appears as squares or replacement characters | Linux CI environment lacks CJK fonts | Install `fonts-noto-cjk` (see Section 6) or run the export on macOS |

---

## Related

- [deck-authoring.md — PPTX Export Contract](deck-authoring.md#pptx-export-contract-deck-stage--export-pptxmjs) — Full specification for the `window.__deck` API, `noscale` attribute, speaker notes format, and 1-indexed numbering contract that decks must implement for tier-1 export.
