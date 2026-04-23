# Structural Fix Reference

Fixes for layout, spacing, simplification, component extraction, responsive adaptation, and typography.

---

## 1. Layout & Spacing

### Spacing System
- Use a consistent spacing scale (framework-provided like Tailwind, or custom tokens)
- Name tokens semantically: `--space-xs` through `--space-xl`
- Use `gap` for sibling spacing instead of margins (eliminates margin collapse)
- Apply `clamp()` for fluid spacing that breathes on larger screens

### Visual Rhythm
- **Tight grouping** for related elements (8-12px between siblings)
- **Generous separation** between distinct sections (48-96px)
- **Varied spacing** within sections -- not every row needs the same gap
- **Asymmetric compositions** -- break the predictable centered-content pattern when appropriate

### Layout Tool Selection
| Need | Tool | When |
|------|------|------|
| 1D layout | Flexbox | Rows, nav bars, button groups, card contents, most component internals |
| 2D layout | Grid | Page structure, dashboards, coordinated rows AND columns |
| Responsive cards | Grid + auto-fit | `repeat(auto-fit, minmax(280px, 1fr))` for breakpoint-free grids |
| Complex pages | Grid + named areas | `grid-template-areas`, redefine at breakpoints |

**Don't default to Grid** when Flexbox with `flex-wrap` would be simpler.

### Visual Hierarchy

- Apply the squint test: blur your eyes -- can you still identify the most important element, the second most important, and clear groupings? If not, the hierarchy isn't working.
- Is hierarchy achieved through space and weight alone?
- Does whitespace guide the eye to what matters?

### Breaking Card Grid Monotony

Card grids where every card has the same icon + heading + text pattern are the most common monotony trap:

- Vary card sizes: span some cards across 2 columns for featured content
- Mix cards with non-card content -- use spacing and alignment to create grouping naturally
- Never nest cards inside cards -- use dividers or spacing for internal hierarchy
- Consider whether cards are needed at all -- spacing and alignment alone often creates sufficient grouping

### Depth & Elevation Management

Build a semantic z-index scale and use it consistently:

```css
/* Semantic z-index scale */
:root {
  --z-dropdown:       100;
  --z-sticky:         200;
  --z-modal-backdrop: 300;
  --z-modal:          400;
  --z-toast:          500;
  --z-tooltip:        600;
}
```

- Build a consistent shadow scale (sm, md, lg, xl) -- shadows should be subtle, not decorative
- Use elevation to reinforce hierarchy, not as visual noise

### Optical Adjustments

- If an icon looks visually off-center despite being geometrically centered, nudge it -- but only when it actually looks wrong, not speculatively
- Never use arbitrary z-index values (999, 9999) -- always reference the semantic scale

### Alignment & Spacing Standardization

When alignment/spacing issues are detected in the audit, apply these fixes:

**Tailwind Scale Normalization** (4pt base: 1=4px, 2=8px, 3=12px, 4=16px, 6=24px, 8=32px, 12=48px, 16=64px):
1. Replace inline `style` spacing values with the nearest Tailwind class (e.g., `style={{padding: '13px'}}` -> `p-3` (12px))
2. Replace arbitrary values with standard scale (e.g., `gap-[7px]` -> `gap-2` (8px))
3. Unify spacing for same-role elements to a single value (e.g., all card gaps -> `gap-4`)
4. Ensure section hierarchy: intra-element (gap-1~2) < inter-element (gap-3~4) < inter-section (gap-6~8)

**Visual Alignment Fix Patterns**:
1. Icon-text alignment: apply `inline-flex items-center gap-1.5` or `gap-2` pattern
2. Form field spacing: unify label-input gap to `space-y-2`, field-to-field gap to `space-y-4`
3. Button groups: unify with `flex items-center gap-2` or `gap-3`
4. List items: apply `items-baseline` when text baseline alignment is needed
5. Horizontal elements: unify with `justify-between` or `justify-start gap-N` (no mixing)

**Verification**:
- Confirm sibling elements within the same container use identical spacing values after fixes
- Confirm icons and text are visually on the same line
- Confirm section spacing hierarchy is correct (intra-element < inter-element < inter-section)

---

## 2. Simplification

### Information Architecture
- **Reduce scope**: Remove secondary actions, optional features, redundant information
- **Progressive disclosure**: Hide complexity behind clear entry points (accordions, modals, step-through flows)
- **Combine related actions**: Merge similar buttons, consolidate forms, group related content
- **Clear hierarchy**: ONE primary action, few secondary, everything else tertiary or hidden
- **Remove redundancy**: If it's said elsewhere, don't repeat it

### Visual Simplification
- **Reduce color palette**: 1-2 colors plus neutrals, not 5-7
- **Limit typography**: One font family, 3-4 sizes max, 2-3 weights
- **Remove decorations**: Eliminate borders, shadows, backgrounds that don't serve hierarchy
- **Flatten structure**: Reduce nesting, remove unnecessary containers -- never nest cards inside cards
- **Remove unnecessary cards**: Use spacing and alignment instead when cards aren't needed

### Interaction Simplification
- **Reduce choices**: Fewer buttons, fewer options, clearer path forward
- **Smart defaults**: Make common choices automatic
- **Inline actions**: Replace modal flows with inline editing where possible
- **Remove steps**: Can the flow be fewer steps?
- **Clear CTAs**: ONE obvious next step, not five competing actions

### Content Simplification

- **Shorter copy**: Cut every sentence in half, then do it again
- **Active voice**: "Save changes" not "Changes will be saved"
- **Remove jargon**: Plain language always wins
- **Scannable structure**: Short paragraphs, bullet points, clear headings
- **Remove redundant copy**: No headers restating intros, no repeated explanations

### Code Simplification

- **Remove unused code**: Dead CSS, unused components, orphaned files
- **Flatten component trees**: Reduce nesting depth where it adds no value
- **Consolidate styles**: Merge similar styles, use utilities consistently
- **Reduce variants**: Does that component need 12 variations, or can 3 cover 90% of cases?

### Document Removed Complexity

If you removed features, options, or copy:
- Note why they were removed (comment in code or PR description)
- Consider if they need alternative access points
- Flag any user feedback to monitor after the change

---

## 3. Component Extraction

### When to Extract

Extract a pattern when ANY of these are true:
- Pattern is used 3+ times, or clearly likely to be reused
- Systematizing would improve consistency across the product
- Pattern is general, not context-specific to one page or flow

Do not extract one-off, context-specific implementations without generalizing them first.

### Extraction Process

1. **Find the design system**: Locate component library, shared UI directory, understand naming conventions and import patterns
2. **Identify patterns**: Repeated components, hard-coded values, inconsistent variations of the same concept
3. **Assess value**: Is this general enough? What variations does it need? What's the maintenance cost vs benefit?
4. **Create components with**: Clear props API with sensible defaults, proper variants, built-in accessibility (ARIA, keyboard nav, focus management), documentation and usage examples
5. **Create tokens with**: Semantic naming (not value-based), proper hierarchy, documentation of when to use each token
6. **Migrate**: Find all instances, replace systematically, test for visual and functional parity, delete dead code
7. **Document**: Update the component library, add examples, update Storybook or component catalog if it exists

### Migration Process Detail

```
1. Find all instances:
   grep -r "ComponentPattern" src/ --include="*.tsx"

2. Replace systematically (one instance at a time, test after each)

3. Run visual comparison before/after

4. Delete old implementation once all instances are migrated

5. Update imports in barrel files
```

### NEVER

- Extract one-off, context-specific implementations without generalization
- Create components so generic they're useless
- Skip proper TypeScript types or prop documentation
- Create tokens for every single value (tokens need semantic meaning)
- Extract without understanding existing design system conventions

---

## 4. Responsive Adaptation

### Mobile (Desktop -> Mobile)
- **Layout**: Single column, vertical stacking, full-width components, bottom navigation
- **Touch targets**: 44x44px minimum, larger tap areas with more spacing
- **Content**: Progressive disclosure, prioritize primary content, shorter text, 16px minimum font
- **Navigation**: Hamburger menu or bottom nav, reduce complexity, sticky headers

### Tablet (Hybrid)
- **Layout**: Two-column layouts, side panels, master-detail views (not single or three-column)
- **Interaction**: Support both touch and pointer
- **Orientation**: Adapt based on portrait vs landscape -- side panels collapse in portrait, show in landscape

### Desktop Adaptation (Mobile -> Desktop)
- **Layout**: Multi-column layouts, side navigation always visible, multiple information panels
- **Interaction**: Hover states, keyboard shortcuts, right-click context menus, drag and drop
- **Content**: Show more information upfront, richer visualizations, more detailed descriptions
- **Constraint**: Add max-width constraints -- don't stretch to 4K

### Print Adaptation
- Remove navigation, footer, and interactive elements
- Page breaks at logical points
- Show full URLs and expand shortened content
- Add page numbers, headers, footers, print date

### Breakpoint Strategy
- Use fluid layouts with `clamp()` to minimize breakpoints
- Prefer content-driven breakpoints over generic ones
- Test at: 320px (small mobile), 375px (standard), 768px (tablet), 1024px (small desktop), 1440px (standard), 1920px (large)
- Prefer `min-width` (mobile-first) media queries

### Container Queries

For components that need to adapt based on their container (not viewport), use container queries:

```css
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}
```

Container queries are superior to media queries for reusable components that appear in different layout contexts.

### Touch Target Checklist
- [ ] All interactive elements >= 44x44px
- [ ] Adequate spacing between touch targets (>= 8px)
- [ ] No hover-only interactions on touch
- [ ] Swipe gestures where appropriate

### Test on Real Devices, Not Just DevTools

Browser DevTools device emulation is helpful for quick checks, but not perfect:
- Test on actual phones and tablets
- Test both orientations (portrait and landscape)
- Test different browsers (Safari iOS, Chrome Android)
- Test with slow connections (throttle in DevTools, or use network throttling)

---

## 5. Typography

### Font Selection Guidance

When choosing or evaluating fonts:
- Does the font match the brand personality? (Playful brand should not use a corporate typeface; financial product should not use a quirky display font)
- Are we using invisible defaults? (Inter, Roboto, Arial, Open Sans are fine for utility, but invisible for brand)
- Use genuine pairing contrast: serif + sans, geometric + humanist. Avoid pairing two similar sans-serifs.
- Alternatively, use one font family in multiple weights -- simpler and often better

### Type Scale
Use a modular scale with fluid sizing:
```css
--text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
--text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
--text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
--text-lg: clamp(1.125rem, 1rem + 0.6vw, 1.25rem);
--text-xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem);
--text-2xl: clamp(1.5rem, 1.2rem + 1.5vw, 2rem);
--text-3xl: clamp(2rem, 1.5rem + 2.5vw, 3rem);
```

### Fixed vs Fluid Sizing Strategy

This distinction matters:

- **App UIs** (dashboards, admin tools, forms): Use a **fixed `rem`-based type scale**. Fluid sizing undermines the spatial predictability that dense, container-based layouts need. Adjust at 1-2 breakpoints if needed.
- **Marketing / content pages** (landing pages, blogs): Use **fluid sizing via `clamp()`** for headings and display text. Keep body text fixed.

### Hierarchy Principles
- Create dramatic size jumps between heading levels (not incremental 2px steps)
- Pair bold weights (700-900) for headings with light weights (300-400) for body
- Use 3-4 sizes maximum for most interfaces
- Line height: 1.2-1.3 for headings, 1.5-1.7 for body text
- Line length: 45-75 characters for body text (`max-width: 65ch`)

### Weight Consistency Rules

- Define clear roles for each weight and stick to them throughout the product
- Do not use Bold in one section and Semibold in another for the same role (heading, label, etc.)
- 3-4 weights is plenty: Regular, Medium, Semibold, Bold
- Load only the weights you actually use (each weight adds to page load)

### Font Loading
```css
@font-face {
  font-display: swap;  /* or optional for non-critical fonts */
}
```
- Subset fonts (only characters needed)
- Preload critical fonts
- Limit font weights loaded (2-3 max)

### Readability Fixes
- Ensure sufficient contrast ratio (4.5:1 for body, 3:1 for large text)
- Add `letter-spacing: 0.02em` for uppercase text
- Use `text-wrap: balance` for headings (prevents orphaned words, even line distribution)
- Use `text-wrap: pretty` for body text (prevents orphans at paragraph end)
- Avoid justified text on narrow columns

### NEVER
- Use more than 2 font families
- Set body text below 16px on mobile
- Use monospace as a lazy "developer tool" aesthetic
- Put large icons with rounded corners above every heading
- Pick sizes arbitrarily -- commit to a scale
- Disable browser zoom (`user-scalable=no`)
- Use `px` for font sizes -- use `rem` to respect user settings
- Pair fonts that are similar but not identical (two geometric sans-serifs look like a mistake)
