---
name: ui-audit
description: >
  Technical UI audit pipeline. Accepts a live URL or source path, resolves source files,
  and scores 5 technical dimensions (Accessibility, Performance, Theming, Responsive, Design System Compliance)
  producing a /20 Technical Audit report with classified issues. Includes Common Component Usage Audit
  and Alignment & Spacing Audit. Use this skill for technical-only UI audits, or let the /ui orchestrator
  invoke it as part of the full pipeline. Triggers on: technical audit, a11y check, performance scan,
  design system compliance, component usage check, spacing audit.
user-invocable: true
argument-hint: "<URL or path> [--viewport WxH]"
---

Technical UI audit: design context loading, target resolution, and 5-dimension technical scoring.

---

## Step 0: Design Context Check

Before auditing, load the project's design baseline:

### 0A: Project Design System (objective, from code)
1. Check if `.ui-snapshot.md` exists at project root
2. If YES -> load it (color tokens, component inventory, spacing scale, font system)
3. If NO -> run `/ui-snapshot` first to generate it, then load
4. Use the snapshot to calibrate all audit scoring:
   - "Hard-coded color" = color NOT in the snapshot's token list
   - "Off-pattern component" = custom component where a shadcn equivalent exists in the snapshot
   - "Inconsistent spacing" = spacing not matching the project's scale

### 0B: Brand & Audience Context (subjective, from user)
1. Check if `.ui-snapshot.md` has a `## Brand Context` section
2. If YES -> load it for brand/audience/aesthetic context
3. If NO -> proceed with defaults (brand context is optional for technical audits)

---

## Step 1: Target Resolution

### URL Input (starts with `http://` or `https://`)

```
1. PARSE URL
   - Extract: origin, pathname, searchParams

2. SCREENSHOT (Playwright)
   - playwright_navigate(url)
   - playwright_screenshot() -> capture viewport
   - playwright_get_visible_html() -> capture rendered DOM
   - playwright_evaluate("document.title") -> page title

3. RESOLVE to source files (Next.js App Router)
   - Strip origin, keep pathname: /portal/plans/free/edit
   - Map to app/ directory structure:
     a. Split pathname into segments: [portal, plans, free, edit]
     b. Walk src/admin-portal/app/ matching segments
     c. For non-matching segments, check for dynamic routes: [name], [id], [slug]
     d. Find page.tsx at the resolved path
   - Collect layout.tsx chain (all ancestor layouts)
   - Trace component imports from page.tsx (recursive, project files only)
   - Result: list of all source files that render this page

4. READ source files for code analysis
```

### Source Path Input (starts with `src/` or relative path)

```
1. Glob for *.tsx, *.ts files under the given path
2. Trace component imports from page.tsx files found
3. No Playwright screenshot (code-only analysis)
```

### Surface Mode Classification

After resolving the target, classify the page's surface mode using [surface-modes.md](reference/surface-modes.md):

| Route Pattern | Surface | Audit Behavior |
|---------------|---------|----------------|
| `/(auth)/*` | Auth / Entry | Brand clarity, visual memorability, conversion hierarchy |
| `/(onboarding)/*` | Onboarding | Progressive clarity, step completion, visual trust |
| `/portal/ai-chat`, `/portal/chat*` | Chat / AI Workspace | Low chrome, conversational rhythm, focus |
| `/portal/*` (all others) | Portal / Operations | Operational clarity, card restraint, accent discipline |

Load surface-specific rules (composition, card policy, copy mode, motion budget) before proceeding to audit.

---

## Step 2: AUDIT (Technical Quality)

Score 5 dimensions (0-4 each, total /20). Read [design-principles.md](reference/design-principles.md) for DO/DON'T reference. Apply surface-specific rules from [surface-modes.md](reference/surface-modes.md) when scoring.

### 2.1 Accessibility (A11y)
- Missing ARIA: interactive elements without roles/labels/states
- Keyboard navigation: missing focus indicators, tab order issues
- Semantic HTML: divs instead of buttons, improper heading hierarchy
- Form issues: inputs without labels, missing error messaging
- **Score**: 0=Inaccessible, 1=Major gaps, 2=Partial, 3=Good (WCAG AA mostly met), 4=Excellent

### 2.2 Performance
- Layout thrashing: reading/writing layout in loops
- Expensive animations: animating width/height instead of transform/opacity
- Missing optimization: no lazy loading, unoptimized images
- Unnecessary re-renders: missing memoization where needed
- **Score**: 0=Severe, 1=Major, 2=Partial, 3=Good, 4=Excellent

### 2.3 Theming
- Hard-coded colors not using CSS variables/tokens
- Broken dark mode: missing dark variants, poor contrast
- Inconsistent token usage, mixing token types
- **Score**: 0=No theming, 1=Minimal, 2=Partial, 3=Good, 4=Excellent

### 2.4 Responsive Design
- Fixed widths that break on mobile
- Touch targets < 44x44px
- Horizontal scroll / content overflow
- Missing breakpoints
- **Score**: 0=Desktop-only, 1=Major issues, 2=Partial, 3=Good, 4=Excellent

### 2.5 Design System Compliance
Check adherence to project's design tokens and component patterns (from `.ui-snapshot.md`):
- Hard-coded colors not in token list, mixed color formats
- Custom components where design system equivalents exist (e.g., custom button instead of shadcn Button)
- Spacing values outside the project's scale, inconsistent border-radius
- Duplicated style constants across files (e.g., same shadow string in multiple components)

**Common Component Usage Audit**:
Analyze the page's import tree and detect cases where functionality is implemented from scratch instead of using common components registered in `.ui-snapshot.md`'s Component Inventory (`components/common/`, `components/ui/`). Report as an issue when a custom implementation pattern is found where a common component alternative exists.

| # | Detection Pattern | Common Component Alternative | Severity |
|---|-------------------|------------------------------|----------|
| 1 | Direct `<table>` usage or raw `@tanstack/react-table` invocation | `DataTable` + `DataTableToolbar` + `DataTablePagination` | P1 |
| 2 | Custom skeleton/spinner implementation (inline animate-pulse, etc.) | `PageSkeleton`, `CardSkeleton`, `TableSkeleton`, `ListSkeleton` | P2 |
| 3 | Inline empty data state handling (conditional "no data" text) | `EmptyState` | P2 |
| 4 | Custom confirmation UI for destructive actions (raw AlertDialog composition) | `ConfirmDialog` | P2 |
| 5 | Inline styles or conditional classes for status display | `StatusBadge` | P2 |
| 6 | Inline error banner implementation | `ErrorBanner` | P2 |
| 7 | Custom title+description+actions layout | `PageHeader` or `CardPageHeader` | P2 |
| 8 | Custom pagination implementation | `DataTablePagination` or `EllipsisPagination` | P2 |
| 9 | Inline disabled+spinner pattern on buttons | `LoadingButton` | P2 |
| 10 | Missing error boundary on pages with async data loading | `ErrorBoundary` | P1 |

Detection procedure:
1. Extract imports from `components/common` in the source files collected during Step 1
2. Cross-reference with `.ui-snapshot.md`'s Component Inventory to identify unused common component candidates
3. Search page code for custom implementation patterns listed in the table above
4. Classify matched items as issues (file:line, replacement component, severity)

**shadcn/ui Coding Pattern Audit**:
Check adherence to shadcn/ui coding conventions (ref: `.claude/skills/shadcn/rules/`).

| # | Detection Pattern | Recommended Fix | Severity |
|---|-------------------|-----------------|----------|
| 1 | `space-x-*` or `space-y-*` usage | Replace with `flex gap-*` or `flex flex-col gap-*` | P2 |
| 2 | `w-N h-N` where N is the same value | Replace with `size-N` | P3 |
| 3 | `dark:` manual color overrides | Use semantic tokens (`bg-background`, `text-foreground`) | P2 |
| 4 | Raw `div` with manual form layout instead of `FieldGroup`/`Field` | Use shadcn Field composition pattern | P3 |
| 5 | Items not inside their Group (`SelectItem` outside `SelectGroup`, etc.) | Wrap items in appropriate Group component | P2 |
| 6 | Dialog/Sheet/Drawer missing Title component | Add `DialogTitle`/`SheetTitle`/`DrawerTitle` (use `sr-only` if hidden) | P1 |
| 7 | Icon sizing classes (`size-4`, `w-4 h-4`) inside Button/component | Remove sizing; use `data-icon` attribute instead | P3 |
| 8 | Hard-coded colors (`bg-blue-500`, `text-red-600`) | Use semantic tokens or Badge variants | P2 |

Detection procedure:
1. Search source code for patterns listed above using regex matching
2. Cross-reference with shadcn skill rules to confirm violations
3. Classify matched items as issues (file:line, recommended fix, severity)

**Alignment & Spacing Audit**:
Analyze page source code and screenshots (when available) to detect alignment and spacing standard violations.

A. Tailwind Standard Scale Compliance:

| # | Detection Pattern | Severity |
|---|-------------------|----------|
| 1 | Arbitrary px/rem spacing in inline styles (e.g., `style={{padding: '13px'}}`) | P1 |
| 2 | Non-standard spacing via Tailwind arbitrary values (e.g., `p-[13px]`, `gap-[7px]`) | P2 |
| 3 | Inconsistent spacing for same-role elements on the same page (e.g., card gaps mixing `gap-4` and `gap-6`) | P1 |
| 4 | Section spacing smaller than element spacing (hierarchy inversion) | P1 |

B. Visual Alignment Consistency:

| # | Detection Pattern | Severity |
|---|-------------------|----------|
| 1 | Vertical misalignment between icon and adjacent text (missing `items-center`) | P1 |
| 2 | Same-level elements using different alignment baselines | P2 |
| 3 | Inconsistent spacing between form labels and input fields | P2 |
| 4 | Missing text baseline alignment in lists/tables | P2 |
| 5 | Uneven spacing between buttons in a button group | P2 |

Detection procedure:
1. Search source code for inline styles and Tailwind arbitrary values (`[...]`) to detect non-standard spacing
2. Compare gap/margin/padding values among sibling elements within the same container to detect inconsistencies
3. Check screenshots (when available) for visual alignment issues (icon-text misalignment, uneven margins, etc.)
4. Classify matched items as issues (file:line, recommended fix, severity)

- **Score**: 0=No system (all ad-hoc), 1=Major gaps, 2=Partial (main tokens used, many overrides), 3=Good (consistent tokens, minor drift), 4=Excellent (fully aligned)

---

## Output Format

Output the Technical Audit report in this exact structure:

```
# Technical Audit -- ?/20

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Accessibility | ?/4 | ... |
| Performance | ?/4 | ... |
| Theming | ?/4 | ... |
| Responsive | ?/4 | ... |
| Design System Compliance | ?/4 | ... |

## Issues by Severity

### P0 Blocking
[list with file:line, category (TECHNICAL/STRUCTURAL/VISUAL/CONTENT), business impact (SAFE/MANUAL_REVIEW)]

### P1 Major
[list]

### P2 Minor
[list]

### P3 Enhancement
[list]

## Metadata
- Surface Mode: {surface}
- Source Files: {count} files analyzed
- Screenshot: {available/not available}
```

---

## References

| Reference | Content |
|-----------|---------|
| [design-principles.md](reference/design-principles.md) | Context protocol, DO/DON'T guidelines, AI slop checklist |
| [surface-modes.md](reference/surface-modes.md) | Surface classification, composition/card/copy/motion rules |
