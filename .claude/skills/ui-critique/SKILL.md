---
name: ui-critique
description: >
  Design/UX critique pipeline. Evaluates a page against AI Slop Detection, Nielsen's 10 Heuristics (/40),
  Cognitive Load Assessment, and Persona-based Red Flags. Requires target resolution (source files + screenshot)
  to already be in conversation context, or performs its own if invoked standalone.
  Use this skill for UX-focused critiques, or let the /ui orchestrator invoke it as part of the full pipeline.
  Triggers on: UX critique, heuristic evaluation, cognitive load, persona test, AI slop detection, usability review.
user-invocable: true
argument-hint: "<URL or path> [--viewport WxH]"
---

Design/UX critique: AI slop detection, Nielsen heuristics scoring, cognitive load assessment, and persona testing.

---

## Prerequisites

This skill works best when invoked after `/ui-audit`, which provides:
- Resolved source files and surface mode classification
- Screenshot (if URL was provided)

If invoked standalone, perform target resolution first:
1. Navigate to URL with Playwright (if URL provided), take screenshot, resolve source files
2. Classify surface mode using [surface-modes.md](reference/surface-modes.md)

---

## Step 3A: AI Slop Detection (Gate Check)

This is the FIRST and PRIMARY critique check. Run the AI Slop Detection Checklist from [design-principles.md](reference/design-principles.md).

**Verdict**:
- **PASS** (0-2 tells): Distinctive, proceed to heuristics
- **WARN** (3-4 tells): Some generic patterns, note specific tells
- **FAIL** (5+ tells): Heavy AI fingerprints -- flag as dominant issue before proceeding

If FAIL, this becomes the primary finding and should drive fix priorities.

---

## Step 3B: Nielsen's 10 Heuristics (/40)

Score each heuristic 0-4 using detailed rubrics from [heuristics-scoring.md](reference/heuristics-scoring.md).

| # | Heuristic | Check For |
|---|-----------|-----------|
| 1 | Visibility of System Status | Loading indicators, action confirmations, progress, active navigation states |
| 2 | Match System & Real World | Familiar terminology, logical order, recognizable icons, domain-appropriate language |
| 3 | User Control & Freedom | Undo/redo, cancel buttons, clear back navigation, escape from processes |
| 4 | Consistency & Standards | Consistent terminology, predictable behavior, platform conventions, visual consistency |
| 5 | Error Prevention | Confirmation dialogs, input constraints, smart defaults, clear labels |
| 6 | Recognition > Recall | Visible options, contextual help, recent items, autocomplete, labeled icons |
| 7 | Flexibility & Efficiency | Keyboard shortcuts, customization, bulk actions, power user features |
| 8 | Aesthetic & Minimalist Design | Only necessary info visible, clear hierarchy, purposeful color, no clutter |
| 9 | Error Recovery | Plain language errors, specific problem identification, actionable suggestions |
| 10 | Help & Documentation | Searchable help, contextual tooltips, task-focused, concise |

**Rating bands**: 36-40 Excellent, 28-35 Good, 20-27 Acceptable, 12-19 Poor, 0-11 Critical

Apply surface-specific rules from [surface-modes.md](reference/surface-modes.md) when scoring -- the same pattern may be acceptable on one surface and an anti-pattern on another.

---

## Step 3C: Cognitive Load Assessment

Run 8-item checklist from [cognitive-load.md](reference/cognitive-load.md):

1. **Choice overload**: >4 visible options at any single decision point
2. **Information density**: Too much data without visual hierarchy or grouping
3. **Navigation depth**: >3 clicks to reach key actions
4. **Inconsistent patterns**: Same concept looks/behaves differently across the page
5. **Hidden state**: User must remember information from previous screens
6. **Interruption cost**: Popups/modals that break the primary task flow
7. **Visual noise**: Decorative elements competing with functional content
8. **Ambiguous actions**: Unclear what will happen when clicking a control

**Severity**: 0-1 failures = low, 2-3 = moderate, 4+ = critical

---

## Step 3D: Persona Red Flags

Auto-select 2-3 personas from [personas.md](reference/personas.md) based on surface mode:

| Surface | Recommended Personas |
|---------|---------------------|
| Portal / Operations | Alex (impatient power user), Sam (accessibility needs), Riley (mobile-first) |
| Auth / Entry | Jordan (cautious first-timer), Alex (impatient), Casey (international user) |
| Chat / AI Workspace | Alex (impatient power user), Sam (accessibility needs) |
| Onboarding | Jordan (cautious first-timer), Riley (mobile-first) |

For each persona:
1. Identify the primary user action on this page
2. Walk through the action as that persona
3. Report specific red flags (not generic observations)
4. If `.ui-snapshot.md` has Brand Context with target audience, generate 1-2 project-specific personas

---

## Step 3E: Targeted Questions (Optional)

Only when invoked as part of `full` pipeline without `--dry-run`:
- Present 2-4 targeted questions based on actual findings from 3A-3D
- Every question must reference a specific finding
- Skip entirely if findings are straightforward (1-2 clear issues with obvious fixes)

---

## Output Format

Output the Design Critique report in this exact structure:

```
# Design Critique -- ?/40

### AI Slop Verdict: PASS/WARN/FAIL -- [specific tells if any]

### Nielsen's 10 Heuristics
| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | ?/4 | ... |
| 2 | Match System & Real World | ?/4 | ... |
| 3 | User Control & Freedom | ?/4 | ... |
| 4 | Consistency & Standards | ?/4 | ... |
| 5 | Error Prevention | ?/4 | ... |
| 6 | Recognition > Recall | ?/4 | ... |
| 7 | Flexibility & Efficiency | ?/4 | ... |
| 8 | Aesthetic & Minimalist | ?/4 | ... |
| 9 | Error Recovery | ?/4 | ... |
| 10 | Help & Documentation | ?/4 | ... |

### Cognitive Load: ?/8 failures -- low/moderate/critical

### Persona Red Flags
**[Name]**: [specific finding]
...

## Issues by Severity

### P0 Blocking
[list with file:line, category, business impact tag]

### P1 Major
[list]

### P2 Minor
[list]

### P3 Enhancement
[list]
```

---

## References

| Reference | Content |
|-----------|---------|
| [design-principles.md](reference/design-principles.md) | Context protocol, DO/DON'T guidelines, AI slop checklist |
| [heuristics-scoring.md](reference/heuristics-scoring.md) | Nielsen heuristics scoring rubric |
| [cognitive-load.md](reference/cognitive-load.md) | Working memory, 8-item checklist |
| [personas.md](reference/personas.md) | Persona-based testing |
| [surface-modes.md](reference/surface-modes.md) | Surface classification, composition/card/copy/motion rules |
