---
name: ui-fix
description: >
  UI fix pipeline. Classifies issues from prior audit/critique, applies fixes in dependency order
  (TECHNICAL -> STRUCTURAL -> VISUAL -> CONTENT -> POLISH), with business logic protection.
  Expects audit and critique results already in conversation context.
  Use this skill to apply UI fixes based on prior audit/critique findings, or let the /ui orchestrator
  invoke it as part of the full pipeline. Triggers on: apply UI fixes, fix issues, normalize, harden,
  polish, apply recommendations.
user-invocable: true
argument-hint: "<URL or path> [--severity P0|P1|P2|P3]"
---

UI fix pipeline: issue classification, dependency-ordered fixing, business logic protection, and verification.

---

## Step 4: Classify Issues

Each finding from prior audit/critique is tagged with:
- **Severity**: P0 (blocking), P1 (major), P2 (minor), P3 (enhancement)
- **Category**: TECHNICAL, STRUCTURAL, VISUAL, CONTENT
- **Business Impact**: SAFE (UI-only change) or MANUAL_REVIEW (touches business logic)

### Category -> Reference Mapping
| Category | Reference File | Scope |
|----------|---------------|-------|
| TECHNICAL | [fix-technical.md](reference/fix-technical.md) | normalize, harden, optimize |
| STRUCTURAL | [fix-structural.md](reference/fix-structural.md) | arrange, distill, extract, adapt, typeset |
| VISUAL | [fix-visual.md](reference/fix-visual.md) | colorize, bolder/quieter, animate, delight, polish |
| CONTENT | [fix-content.md](reference/fix-content.md) | clarify, onboard |

Only fix issues at or above the severity threshold (default: P1 = fix P0+P1).

---

## Step 5: FIX Pipeline

### Business Logic Protection (CRITICAL)

Before applying ANY fix, classify the change:

**SAFE (auto-apply)**:
- CSS classes, Tailwind utilities
- ARIA attributes, role, label additions
- Visual properties (color tokens, spacing, font-size, shadow)
- Layout structure (flex/grid, ordering, margins)
- Animation/transition additions
- UI-only component wrapping (Suspense, ErrorBoundary)

**NO-TOUCH (never modify)**:
- API calls (get, post, put, delete)
- State management (useState, useReducer, Zustand)
- Event handler business logic (onSubmit API calls)
- Conditional rendering business conditions (permissions, plan status, feature flags)
- Routing logic (redirect, push, replace)
- Data transformations (transform, map, filter)
- Form validation rules

**MANUAL_REVIEW (ask user first)**:
When a UI fix requires touching code in the No-Touch zone:
1. Stop auto-fix for that issue
2. Present the issue, proposed change, and impact to user
3. Offer 2-3 safe alternatives (e.g., "CSS-only fix" vs "extract component then modify")
4. Apply only after explicit user approval

### Fix Order (dependency-based)

Apply fixes in this order, loading only the reference files for categories with findings:

1. **TECHNICAL** -> Read [fix-technical.md](reference/fix-technical.md)
   - Design system normalization, hardening, performance optimization

2. **STRUCTURAL** -> Read [fix-structural.md](reference/fix-structural.md)
   - Layout & spacing, simplification, responsive adaptation, typography, component extraction

3. **VISUAL** -> Read [fix-visual.md](reference/fix-visual.md)
   - Color, visual weight, animation, delight, advanced effects

4. **CONTENT** -> Read [fix-content.md](reference/fix-content.md)
   - UX writing, onboarding

5. **POLISH** (always last) -- 23-item final quality checklist:
   - Visual: grid alignment, optical adjustments, responsive spacing, consistent hierarchy, body line length 45-75ch, tinted neutrals (no pure gray)
   - Interaction: every interactive element has default/hover/focus/active/disabled/loading/error/success states, focus indicators visible, keyboard navigation works, logical tab order
   - Transitions: all state changes animated (150-300ms), consistent easing (ease-out-quart/quint/expo), 60fps transform+opacity only, respects prefers-reduced-motion
   - Content: consistent terminology and capitalization, no typos, appropriate length, punctuation consistency
   - Edge cases: loading states for all async actions, helpful empty states (not blank), clear error messages with recovery, long content handled (truncation/wrapping), no layout shift (CLS)
   - Responsiveness: mobile/tablet/desktop tested, touch targets 44x44px minimum, no text < 14px on mobile, no horizontal scroll
   - Code: no console.log, no commented code, no unused imports, no hard-coded colors, proper ARIA and semantic HTML

### Fix Execution

For each fix:
1. Identify the target file and line
2. Check business impact classification (SAFE vs MANUAL_REVIEW)
3. If SAFE: apply the change using Edit tool
4. If MANUAL_REVIEW: skip, log to report, ask user later
5. Log the change: `{file}:{line} - {what changed} - {why}`

---

## Step 6: Verify & Report

### If URL was provided (Playwright available):
1. Reload the page in Playwright
2. Take new screenshot
3. Compare before/after visually
4. Report changes with before/after context

### Output Format

```
## Changes Applied
- {file}: {description of change}
...

## Manual Review Required
- {issue}: {why it needs manual review} -> {recommended approach}
...

## Remaining Issues (below severity threshold)
- {count} P2 issues, {count} P3 issues
- Run `/ui-fix <target> --severity P2` to address these
```

---

## Additional References

These reference files provide deep guidance and are loaded on-demand per category:

| Reference | Content |
|-----------|---------|
| [fix-technical.md](reference/fix-technical.md) | Normalization, hardening, performance |
| [fix-structural.md](reference/fix-structural.md) | Layout, spacing, responsive, typography, component extraction |
| [fix-visual.md](reference/fix-visual.md) | Color, animation, delight, effects |
| [fix-content.md](reference/fix-content.md) | UX writing, onboarding |
| [typography.md](reference/typography.md) | Type scales, pairing, loading strategies |
| [color-and-contrast.md](reference/color-and-contrast.md) | OKLCH, palettes, dark mode, contrast |
| [spatial-design.md](reference/spatial-design.md) | Grids, rhythm, container queries |
| [motion-design.md](reference/motion-design.md) | Easing, duration, spring physics |
| [interaction-design.md](reference/interaction-design.md) | States, feedback, affordance |
| [responsive-design.md](reference/responsive-design.md) | Breakpoints, fluid layouts |
| [ux-writing.md](reference/ux-writing.md) | Microcopy, tone, clarity |
