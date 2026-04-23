#!/usr/bin/env node
/**
 * measure-baseline.mjs
 *
 * Baseline measurement script for editable PPTX export compatibility.
 * Phase 1: Static analysis of each deck's HTML source (no browser required).
 * Phase 4: Replace with live Playwright measurements for runtime checks.
 *
 * Usage:
 *   node .claude/skills/design-artifact/scripts/measure-baseline.mjs
 *   node .claude/skills/design-artifact/scripts/measure-baseline.mjs --json
 *   node .claude/skills/design-artifact/scripts/measure-baseline.mjs --output path/to/out.json
 *
 * Output: JSON summary + per-deck results.
 */

import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '../../../..'); // scripts/ → design-artifact/ → skills/ → .claude/ → project root

// ---------------------------------------------------------------------------
// Deck registry (plan tranquil-wiggling-gosling.md §1.5, 7 targets)
// ---------------------------------------------------------------------------
const DECKS = [
  {
    id: 'onboarding-first-week-deck',
    path: 'designs/onboarding-first-week-deck/index.html',
    tier: 'Tier 2',
    notes: '13 sections, 한글. window.__deck 존재하나 getSlideCount/goToSlide 확인 필요',
  },
  {
    id: 'clawpod-customer-intro',
    path: 'designs/clawpod-customer-intro.html',
    tier: 'Tier 1',
    notes: '15 sections, 다크모드. window.__deck 구현 완료 (line 475~)',
  },
  {
    id: 'agent-create-wizard',
    path: 'designs/agent-create-wizard/index.html',
    tier: 'Tier 3',
    notes: '와이어프레임, 단일 페이지, deck-stage 없음',
  },
  {
    id: 'marketing-landing',
    path: 'designs/marketing-landing/index.html',
    tier: 'Tier 3',
    notes: '랜딩 페이지, section 3개, deck-stage 없음',
  },
  {
    id: 'onboarding-intro-animation',
    path: 'designs/onboarding-intro-animation/index.html',
    tier: 'Tier 3',
    notes: '애니메이션 전용 (rAF 루프). freeze hook 없음. R13 실측 대상',
  },
  {
    id: 'payment-flow-wireframe',
    path: 'designs/payment-flow-wireframe/index.html',
    tier: 'Tier 3',
    notes: '와이어프레임, deck-stage 없음',
  },
  {
    id: 'clawpod-customer-intro-dir',
    path: 'designs/clawpod-customer-intro',
    tier: 'N/A',
    notes: 'R15: 이전 버전 디렉토리 잔재. index.html 없으면 측정 제외',
  },
];

// ---------------------------------------------------------------------------
// File reader (sync, handles file vs directory)
// ---------------------------------------------------------------------------
function readHtmlSync(relPath) {
  const abs = resolve(PROJECT_ROOT, relPath);
  if (!existsSync(abs)) return null;
  try {
    return readFileSync(abs, 'utf-8');
  } catch (e) {
    if (e.code === 'EISDIR') {
      const idx = resolve(abs, 'index.html');
      if (!existsSync(idx)) return null;
      return readFileSync(idx, 'utf-8');
    }
    return null;
  }
}

// ---------------------------------------------------------------------------
// Static analysis checks
// ---------------------------------------------------------------------------

/**
 * vector_tier1: window.__deck with getSlideCount + goToSlide defined in source.
 */
function checkTier1(html) {
  return /window\.__deck/.test(html) &&
         /getSlideCount/.test(html) &&
         /goToSlide/.test(html);
}

/**
 * vector_structure_ok: deck-stage element + <section> children + 1920 canvas width.
 */
function checkStructure(html) {
  return /deck-stage/.test(html) &&
         /<section/.test(html) &&
         /1920/.test(html);
}

/**
 * vector_shadow_dom_ok: no attachShadow usage (static heuristic).
 * Returns: true (safe) | null (undetermined — needs runtime check)
 */
function checkShadowDom(html) {
  return /attachShadow|shadowRoot/.test(html) ? null : true;
}

/**
 * vector_cors_ok: external resources (img/script/link) have crossorigin="anonymous"
 * or are same-origin. Returns { ok: bool, problemCount: number }.
 */
function checkCors(html) {
  const extRe = /<(?:img|script|link)[^>]+(?:src|href)=["']https?:\/\/[^"']+["'][^>]*>/gi;
  const matches = [...(html.matchAll(extRe) || [])];
  const without = matches.filter(m => !m[0].includes('crossorigin'));
  return { ok: without.length === 0, problemCount: without.length };
}

/**
 * vector_animation_freezable: freeze hook present OR no active animations.
 * Returns { ok: bool, warn: bool, hasFreezeHook: bool, hasActiveAnimation: bool }
 */
function checkAnimationFreezable(html) {
  const hasFreezeHook = /freezeForExport/.test(html);
  const hasRaf = /requestAnimationFrame/.test(html);
  const hasKeyframes = /@keyframes/.test(html);
  const hasSetInterval = /setInterval/.test(html);
  const hasCssAnim = /animation\s*:\s*(?!none)/.test(html);
  const hasActive = hasRaf || hasKeyframes || hasSetInterval || hasCssAnim;

  if (hasFreezeHook) return { ok: true, warn: false, hasFreezeHook: true, hasActiveAnimation: hasActive };
  if (!hasActive) return { ok: true, warn: false, hasFreezeHook: false, hasActiveAnimation: false };
  // Has animation but no freeze hook → WARN (not full FAIL, 500ms fallback applies)
  return { ok: false, warn: true, hasFreezeHook: false, hasActiveAnimation: true };
}

/**
 * Determine migration requirement label.
 */
function determineMigration(r) {
  if (!r.file_exists) return '없음 (파일 없음/제외)';
  if (r.vector_ready) return '불필요';
  const needs = [];
  if (!r.vector_tier1) needs.push('Tier 1 API 추가 (필수)');
  if (!r.vector_structure_ok) needs.push('deck-stage 구조 추가 (필수)');
  if (!r.vector_cors_ok) needs.push(`crossorigin 추가 (${r.vector_cors_problem_count}개 리소스, 권장)`);
  if (r.vector_animation_freezable === false) needs.push('freeze hook 추가 (권장)');
  if (r.vector_shadow_dom_ok === null) needs.push('shadow DOM 스코프 런타임 확인 필요');
  return needs.length ? needs.join('; ') : '검토 필요';
}

// ---------------------------------------------------------------------------
// Per-deck measurement
// ---------------------------------------------------------------------------
function measureDeck(deck) {
  const html = readHtmlSync(deck.path);

  if (!html) {
    return {
      id: deck.id,
      path: deck.path,
      tier: deck.tier,
      file_exists: false,
      vector_tier1: false,
      vector_structure_ok: false,
      vector_shadow_dom_ok: null,
      vector_cors_ok: false,
      vector_cors_problem_count: 0,
      vector_animation_freezable: null,
      vector_animation_freezable_warn: false,
      vector_animation_has_active: false,
      vector_ready: false,
      migration_needed: '없음 (파일 없음/제외)',
      notes: deck.notes,
      measurement_method: 'static',
    };
  }

  const tier1 = checkTier1(html);
  const structureOk = checkStructure(html);
  const shadowOk = checkShadowDom(html);
  const cors = checkCors(html);
  const anim = checkAnimationFreezable(html);

  // vector_ready: conservative — null shadowOk treated as undetermined (not blocking)
  const vectorReady =
    tier1 &&
    structureOk &&
    shadowOk !== false &&    // false=fail; null=undetermined (tolerated in static pass)
    cors.ok &&
    anim.ok;                 // warn-only (false+warn) treated as not ready

  const result = {
    id: deck.id,
    path: deck.path,
    tier: deck.tier,
    file_exists: true,
    vector_tier1: tier1,
    vector_structure_ok: structureOk,
    vector_shadow_dom_ok: shadowOk,              // true | null
    vector_cors_ok: cors.ok,
    vector_cors_problem_count: cors.problemCount,
    vector_animation_freezable: anim.ok,
    vector_animation_freezable_warn: anim.warn,
    vector_animation_has_active: anim.hasActiveAnimation,
    vector_ready: vectorReady,
    migration_needed: null,
    notes: deck.notes,
    measurement_method: 'static',
  };

  result.migration_needed = determineMigration(result);
  return result;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
function main() {
  const args = process.argv.slice(2);
  const jsonMode = args.includes('--json');
  const outputIdx = args.indexOf('--output');
  const outputPath = outputIdx >= 0 ? resolve(args[outputIdx + 1]) : null;

  const results = DECKS.map(measureDeck);

  const summary = {
    measured_at: new Date().toISOString(),
    measurement_method: 'static',
    note: 'PHASE 1 static baseline. PHASE 4 replaces with live Playwright measurements for runtime checks (shadow DOM scope, headless drift, actual animation state).',
    total: results.length,
    vector_ready_count: results.filter(r => r.vector_ready).length,
    tier1_count: results.filter(r => r.vector_tier1).length,
    animation_freezable_false_count: results.filter(r => r.vector_animation_freezable === false).length,
    cors_ok_false_count: results.filter(r => r.vector_cors_ok === false).length,
    decks: results,
  };

  if (outputPath) {
    mkdirSync(dirname(outputPath), { recursive: true });
    writeFileSync(outputPath, JSON.stringify(summary, null, 2));
    console.error(`Baseline written to: ${outputPath}`);
  }

  if (jsonMode) {
    process.stdout.write(JSON.stringify(summary, null, 2) + '\n');
    return summary;
  }

  // Human-readable output
  console.log('\n=== Vector Compat Baseline (PHASE 1 Static Analysis) ===\n');
  console.log(`Measured at  : ${summary.measured_at}`);
  console.log(`Total decks  : ${summary.total}`);
  console.log(`vector_ready : ${summary.vector_ready_count}/${summary.total}`);
  console.log(`tier1        : ${summary.tier1_count}/${summary.total}`);
  console.log(`anim_freezable=false : ${summary.animation_freezable_false_count}/${summary.total} (R13 risk)`);
  console.log(`cors_ok=false        : ${summary.cors_ok_false_count}/${summary.total}`);
  console.log('\n--- Per-deck ---\n');

  for (const r of results) {
    const status = r.vector_ready ? 'READY    ' : 'NOT-READY';
    console.log(`[${status}] ${r.id} (${r.tier})`);
    if (!r.file_exists) {
      console.log(`  (file not found — excluded)`);
      continue;
    }
    console.log(`  tier1=${r.vector_tier1}  structure=${r.vector_structure_ok}  shadow=${r.vector_shadow_dom_ok ?? 'undetermined'}  cors=${r.vector_cors_ok}  anim_freeze=${r.vector_animation_freezable}`);
    if (r.vector_animation_freezable === false) {
      console.log(`  *** R13 WARN: active animations, no freeze hook — 500ms fallback will apply ***`);
    }
    if (!r.vector_cors_ok) {
      console.log(`  cors problems: ${r.vector_cors_problem_count} external resource(s) without crossorigin`);
    }
    console.log(`  migration: ${r.migration_needed}`);
  }

  console.log('\nNote: shadow_dom=undetermined requires live Playwright check (PHASE 4).\n');
  return summary;
}

main();
