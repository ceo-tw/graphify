# Design Principles Reference

Consolidated guide for creating distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics.

---

## 1. Context Gathering Protocol

Design skills produce generic output without project context. Confirm design context before doing any design work.

**Required context (minimum):**
- **Target audience**: Who uses this product and in what context?
- **Use cases**: What jobs are they trying to get done?
- **Brand personality/tone**: How should the interface feel?

**Gathering order:**
1. **Check current instructions**: If loaded instructions already contain a **Design Context** section, proceed immediately.
2. **Check .impeccable.md**: Read `.impeccable.md` from the project root. If it exists and contains the required context, proceed.
3. **Ask the user**: If neither source has context, ask the user directly. Do NOT attempt to infer context from the codebase -- code tells you what was built, not who it's for or what it should feel like.

---

## 2. DO/DON'T Guidelines

### Typography

| DO | DON'T |
|----|-------|
| Use a modular type scale with fluid sizing (clamp) | Use overused fonts: Inter, Roboto, Arial, Open Sans, system defaults |
| Vary font weights and sizes for clear visual hierarchy | Use monospace typography as lazy shorthand for "technical/developer" vibes |
| Choose beautiful, unique fonts; pair distinctive display with refined body | Put large icons with rounded corners above every heading |

### Color & Theme

| DO | DON'T |
|----|-------|
| Use modern CSS color functions (oklch, color-mix, light-dark) | Use gray text on colored backgrounds -- use a shade of the background instead |
| Tint neutrals toward brand hue for subconscious cohesion | Use pure black (#000) or pure white (#fff) -- always tint |
| Commit to a cohesive palette with dominant colors and sharp accents | Use the AI color palette: cyan-on-dark, purple-to-blue gradients, neon accents on dark |
| | Use gradient text for "impact" -- especially on metrics or headings |
| | Default to dark mode with glowing accents |

### Layout & Space

| DO | DON'T |
|----|-------|
| Create visual rhythm through varied spacing -- tight groupings, generous separations | Wrap everything in cards -- not everything needs a container |
| Use fluid spacing with clamp() that breathes on larger screens | Nest cards inside cards -- flatten the hierarchy |
| Use asymmetry and unexpected compositions; break the grid for emphasis | Use identical card grids (same-sized cards with icon + heading + text, repeated) |
| | Use the hero metric layout template (big number, small label, gradient accent) |
| | Center everything -- left-aligned with asymmetric layouts feels more designed |
| | Use the same spacing everywhere -- without rhythm, layouts feel monotonous |

### Visual Details

| DO | DON'T |
|----|-------|
| Use intentional, purposeful decorative elements that reinforce brand | Use glassmorphism everywhere (blur, glass cards, glow borders) decoratively |
| | Use rounded elements with thick colored border on one side |
| | Use sparklines as decoration -- tiny charts that convey nothing meaningful |
| | Use rounded rectangles with generic drop shadows |
| | Use modals unless there's truly no better alternative |

### Motion

| DO | DON'T |
|----|-------|
| Use motion to convey state changes -- entrances, exits, feedback | Animate layout properties (width, height, padding, margin) -- use transform and opacity only |
| Use exponential easing (ease-out-quart/quint/expo) for natural deceleration | Use bounce or elastic easing -- they feel dated and tacky |
| For height animations, use grid-template-rows transitions | |
| Focus on high-impact moments: one well-orchestrated page load > scattered micro-interactions | |

### Interaction

| DO | DON'T |
|----|-------|
| Use progressive disclosure -- start simple, reveal sophistication through interaction | Repeat the same information -- redundant headers, intros that restate headings |
| Design empty states that teach the interface, not just say "nothing here" | Make every button primary -- use ghost buttons, text links, secondary styles |
| Make every interactive surface feel intentional and responsive | |
| Use optimistic UI -- update immediately, sync later | |

### Responsive

| DO | DON'T |
|----|-------|
| Use container queries (@container) for component-level responsiveness | Hide critical functionality on mobile -- adapt, don't amputate |
| Adapt the interface for different contexts -- don't just shrink it | |

### UX Writing

| DO | DON'T |
|----|-------|
| Make every word earn its place | Repeat information users can already see |

---

## 3. AI Slop Detection Checklist

**The test**: If you showed this interface to someone and said "AI made this," would they believe you immediately? If yes, that's the problem.

A distinctive interface should make someone ask "how was this made?" not "which AI made this?"

**Common AI fingerprints (2024-2025):**
- [ ] Cyan-on-dark, purple-to-blue gradients, neon accents on dark backgrounds
- [ ] Dark mode with glowing accents as default
- [ ] Gradient text on metrics or headings
- [ ] Glassmorphism everywhere (blur, glass cards, glow borders)
- [ ] Identical card grids: same-sized cards with icon + heading + text
- [ ] Hero metric layout: big number, small label, gradient accent
- [ ] Rounded rectangles with generic drop shadows
- [ ] Overused fonts: Inter, Roboto, Arial, Open Sans
- [ ] Monospace typography for "technical" aesthetic
- [ ] Large icons with rounded corners above every heading
- [ ] Nested cards (cards inside cards)
- [ ] Everything centered with uniform spacing
- [ ] Pure black (#000) and pure white (#fff)
- [ ] Gray text on colored backgrounds
- [ ] Bounce/elastic easing
- [ ] Sparklines as decoration
- [ ] Rounded elements with thick colored border on one side
- [ ] Every button is primary-styled

---

## 4. Implementation Principles

1. **Match complexity to vision**: Maximalist designs need elaborate code with extensive animations and effects. Minimalist designs need restraint, precision, and careful attention to spacing, typography, and subtle details.

2. **Commit to a bold direction**: Pick a clear aesthetic (brutally minimal, maximalist, retro-futuristic, organic, luxury, playful, editorial, brutalist, art deco, soft/pastel, industrial, etc.) and execute with precision. Bold maximalism and refined minimalism both work -- the key is intentionality, not intensity.

3. **Never converge**: No two designs should look the same. Vary between light and dark themes, different fonts, different aesthetics. Never default to common choices across generations.

4. **Identify the differentiator**: What makes this unforgettable? What's the one thing someone will remember?

5. **Production-grade output**: Code must be functional, visually striking, cohesive with a clear aesthetic point-of-view, and meticulously refined in every detail.

---

## Related References

Detailed guidance for each domain:
- [Typography](typography.md) -- scales, pairing, loading strategies
- [Color & Contrast](color-and-contrast.md) -- OKLCH, palettes, dark mode
- [Spatial Design](spatial-design.md) -- grids, rhythm, container queries
- [Motion Design](motion-design.md) -- timing, easing, reduced motion
- [Interaction Design](interaction-design.md) -- forms, focus, loading patterns
- [Responsive Design](responsive-design.md) -- mobile-first, fluid design, container queries
- [UX Writing](ux-writing.md) -- labels, errors, empty states
