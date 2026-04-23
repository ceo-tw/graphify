---
name: ui
description: >
  Unified UI improvement pipeline orchestrator. Routes to specialized sub-skills: /ui-audit (technical /20),
  /ui-critique (design /40), /ui-fix (apply fixes). Accepts a live URL or source path.
  Use this skill whenever the user mentions: UI review, design audit, accessibility check, performance review,
  polish, normalize, responsive, typography, color, layout, animation, UX writing, simplify, harden, optimize,
  cognitive load, usability heuristics, persona test.
  Also triggers when a user passes a URL and asks to improve, review, or fix the page.
user-invocable: true
argument-hint: "<URL or path> [--severity P0|P1|P2|P3] [--dry-run]"
---

Unified UI quality pipeline orchestrator. Routes to specialized sub-skills for focused execution with reduced context load.

---

## Sub-command Router

Parse the first argument to determine the command:

| Input Pattern | Command | Route |
|---------------|---------|-------|
| `setup` | SETUP | Inline (brand context gathering below) |
| `audit <target>` | AUDIT | Invoke `/ui-audit <target>` |
| `critique <target>` | CRITIQUE | Invoke `/ui-critique <target>` |
| `fix <target>` | FIX | Invoke `/ui-fix <target>` |
| `full <target>` | FULL | Sequential: `/ui-audit` -> `/ui-critique` -> `/ui-fix` |
| `<URL or path>` (no command) | FULL | Default to full pipeline |

**Flags** (passed through to sub-skills):
- `--severity P0|P1|P2|P3`: Fix threshold (default: P1 = fix P0+P1), passed to `/ui-fix`
- `--dry-run`: Run audit + critique only, skip fix
- `--viewport WxH`: Screenshot viewport size (default: 1440x900), passed to `/ui-audit` and `/ui-critique`

---

## SETUP Command (inline)

Interactive brand context gathering, appended to `.ui-snapshot.md`:

1. Check if `.ui-snapshot.md` exists at project root
   - If NO -> run `/ui-snapshot` first to generate it
2. Check if `.ui-snapshot.md` has a `## Brand Context` section
   - If YES -> show current brand context, ask if user wants to update
   - If NO -> proceed to gather brand context:
     a. **Explore codebase** for brand clues: README, package.json, existing component styles, color variables, font choices, imagery patterns
     b. **Ask user** focused questions (only what cannot be inferred from code):
        - Target users & primary use cases
        - Brand personality / tone (e.g., "professional but warm", "playful and bold")
        - Aesthetic preferences or anti-references ("not like X", "inspired by Y")
        - Accessibility requirements beyond WCAG AA
     c. **Synthesize** into `## Brand Context` section with subsections: Product, Target Audience, Brand Personality, Visual Direction, Anti-references, Design Priorities
     d. **Append** to `.ui-snapshot.md`

---

## FULL Pipeline Execution

When command is `full` or default (URL/path with no command):

### 1. Run Technical Audit
```
Invoke Skill("ui-audit", "<target> [--viewport WxH]")
```
Produces: Technical Audit /20 score + issues list

### 2. Run Design Critique
```
Invoke Skill("ui-critique", "<target> [--viewport WxH]")
```
Produces: Design Critique /40 score + AI slop verdict + cognitive load + persona flags + issues list

### 3. Check dry-run flag
If `--dry-run`: aggregate scores, output combined report, STOP here.

### 4. Run Fix Pipeline
```
Invoke Skill("ui-fix", "<target> [--severity P1]")
```
Produces: changes applied + manual review list + remaining issues

### 5. Aggregate Final Report

```
# UI Quality Report: {page title or path}

## Combined Score: ?/60 (Audit ?/20 + Critique ?/40)

[Include full audit report from Step 1]

[Include full critique report from Step 2]

[Include fix report from Step 4, if applicable]
```

---

## Sub-Skill Reference

| Skill | Responsibility | Invocation |
|-------|---------------|------------|
| `/ui-audit` | Steps 0-1-2: Design context, target resolution, 5-dimension technical audit | `Skill("ui-audit", "<target>")` |
| `/ui-critique` | Step 3: AI slop, Nielsen heuristics, cognitive load, persona testing | `Skill("ui-critique", "<target>")` |
| `/ui-fix` | Steps 4-5-6: Classification, fix pipeline, verification | `Skill("ui-fix", "<target> --severity P1")` |
| `/ui-snapshot` | Generate design system snapshot | `Skill("ui-snapshot")` |
