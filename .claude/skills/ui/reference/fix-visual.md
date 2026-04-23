# Visual Fix Reference

Consolidated techniques for diagnosing and fixing common visual issues.

---

## 1. Color Issues

### Diagnosis

- **Color absence**: Pure grayscale, limited neutrals, one timid accent
- **Missed semantic meaning**: No color distinction for success/error/warning/info states
- **Pure grays/blacks**: Using `#f5f5f5`, `#000`, `#fff` without tinting

### Palette Strategy

- Pick 2-4 colors beyond neutrals. More is chaos.
- **60/30/10 rule**: Dominant color (60%), secondary (30%), accent (10%), neutrals fill the rest. This creates visual hierarchy without chaos.
- Use OKLCH for perceptually uniform color scales -- equal steps in lightness *look* equal.

**OKLCH concrete examples:**
```css
/* Warm neutral background (subtle warm tint) */
background: oklch(97% 0.01 60);

/* Cool neutral background (subtle cool tint) */
background: oklch(97% 0.01 250);

/* These replace dead #f5f5f5 with life */
```

### Semantic Color

| State   | Tones                          |
|---------|--------------------------------|
| Success | Green (emerald, forest, mint)  |
| Error   | Red/pink (rose, crimson, coral)|
| Warning | Orange/amber                   |
| Info    | Blue (sky, ocean, indigo)      |
| Neutral | Slate for inactive states      |

### Where to Apply Color

- **Status badges**: Colored backgrounds or borders for states
- **Primary actions**: Color the most important CTA
- **Icons**: Colorize for recognition and personality
- **Links**: Colored clickable text (maintain contrast)
- **Accent borders**: Colored left/top borders on cards
- **Tinted backgrounds**: Replace pure gray with warm neutrals `oklch(97% 0.01 60)` or cool tints `oklch(97% 0.01 250)`
- **Typography**: Brand color on section headings (maintain contrast)
- **Decorative elements**: Geometric shapes, soft blobs, subtle gradients in brand colors as background elements

### Data Visualization Color Strategy

- Use color to encode categories or values
- Assign colors systematically -- same category always same color
- Test color combinations for color blindness (especially red/green)
- Use color intensity (heatmap) for density or importance
- Always provide a label or legend alongside color encoding

### Balance & Refinement

After adding color, verify:
- **Dominant** (60%): Primary brand/accent color applied to most colored elements
- **Secondary** (30%): Supporting color for variety without chaos
- **Accent** (10%): High contrast for key moments only
- **Neutrals** (remaining): Background, text, structure -- let these do the heavy lifting

### Accessibility

- WCAG contrast: 4.5:1 for text, 3:1 for UI components
- Never rely on color alone -- add icons/labels/patterns
- Test red/green combinations for color blindness

### NEVER

- Use every color in the rainbow
- Apply color randomly without semantic meaning
- Put gray text on colored backgrounds -- use a darker shade of that color or transparency
- Use pure gray for neutrals -- add subtle color tint (warm or cool)
- Use pure black or pure white for large areas
- Default to purple-blue gradients (AI slop)

---

## 2. Visual Weight

### 2a. Too Safe / Bland

**Symptoms**: Generic fonts, basic colors, everything medium-sized, low contrast, nothing stands out.

#### Typography Amplification

- Swap system fonts for distinctive choices
- Create dramatic size jumps (3-5x, not 1.5x) -- a heading that's only slightly larger than body text has no presence
- Pair weight 900 with weight 200, not 600 with 400 -- extreme weight contrast is what creates drama
- Use variable fonts, display fonts for headlines, condensed/extended widths
- Monospace as intentional accent (not as lazy "dev tool" default)

#### Color Intensification

- Shift to more vibrant, energetic colors (not neon)
- Let one bold color own 60% of the design
- Replace pure grays with tinted grays
- Use intentional multi-stop gradients (not generic purple-to-blue AI slop)
- Sharp accents: high-contrast accent colors that pop against neutrals

#### Spatial Drama

- Make important elements 3-5x larger than surroundings
- Break the grid: let hero elements escape containers
- Use asymmetric layouts with tension -- centered balanced layouts feel safe and forgettable
- Generous whitespace (100-200px gaps, not 20-40px)
- Layer elements with intentional overlap for depth

#### Composition Boldness

- Create clear focal points with dramatic treatment -- the ONE hero moment
- Diagonal flows: escape horizontal/vertical rigidity
- Full-bleed elements: use full viewport width/height for impact
- Unexpected proportions: try 70/30 or 80/20 splits instead of equal columns

#### Visual Effects

- Large soft shadows for elevation (not generic drop shadows on rounded rectangles)
- Texture and depth: grain, halftone, duotone -- NOT glassmorphism (overused AI slop)
- Background treatments: mesh patterns, noise textures, geometric patterns
- Custom illustrative elements that reinforce brand

#### AI Slop Trap Warning

When making things bolder, AI defaults to: cyan/purple gradients, glassmorphism, neon accents on dark backgrounds, gradient text on metrics. These are the OPPOSITE of bold -- they're generic. Bold means distinctive, not "more effects."

**The test**: If you showed this to someone and said "AI made this bolder," would they believe you immediately? If yes, start over.

#### NEVER (Bolder)

- Add effects randomly (chaos is not bold)
- Sacrifice readability for aesthetics
- Make everything bold (then nothing is)
- Copy trendy aesthetics blindly

### 2b. Too Aggressive / Loud

**Symptoms**: Overly saturated colors, extreme contrast everywhere, too many bold elements competing, excessive animation, visual clutter.

#### Color Refinement

- Reduce saturation to 70-85%
- Replace bright colors with muted, sophisticated tones
- Fewer colors used more thoughtfully
- Let neutrals dominate, color as 10% accent
- Tinted grays (warm or cool) instead of pure gray
- Never gray text on colored backgrounds -- use a darker shade of that color or transparency

#### Visual Weight Reduction

- Reduce font weights: 900 to 600, 700 to 500
- Use weight, size, and space for hierarchy instead of color and boldness
- Increase breathing room
- Reduce border thickness, decrease opacity, or remove entirely

#### Composition Refinement

- Reduce scale jumps: smaller contrast between sizes creates calmer feeling
- Align to grid: bring rogue elements back into systematic alignment
- Even out spacing: replace extreme spacing variations with consistent rhythm

#### Simplification

- Remove decorative gradients, shadows, patterns that lack purpose
- Reduce border radius extremes
- Flatten visual hierarchy where possible
- Remove blur effects, glows, multiple shadows

#### Motion Reduction

- Shorter distances (10-20px not 40px), gentler easing
- Remove decorative animations, keep functional motion
- Use ease-out-quart for understated motion
- Remove animations entirely if they serve no clear purpose

#### "Quiet Doesn't Mean Boring" Principle

Quiet design is confident design. It doesn't need to shout. The goal is refined, sophisticated, and easier on the eyes -- think luxury, not laziness. Hierarchy still matters; some elements still need to anchor the composition.

#### NEVER (Quieter)

- Make everything same size/weight (hierarchy still matters)
- Remove all color (quiet is not grayscale)
- Eliminate all personality
- Make everything small and light (some anchors needed)

---

## 3. Animation and Motion

### 4-Layer Animation Strategy

Plan animations across four layers of purpose:

1. **Hero moment**: The ONE signature animation (page load? hero section? key interaction?) -- make this extraordinary
2. **Feedback layer**: Every interaction that needs acknowledgment (button clicks, form submission, toggles)
3. **Transition layer**: State changes that need smoothing (show/hide, page changes, loading)
4. **Delight layer**: Where to surprise and delight (success states, empty states, easter eggs)

**Principle**: One well-orchestrated experience beats scattered animations everywhere. Focus on high-impact moments.

### Timing Reference

| Purpose           | Duration   |
|-------------------|------------|
| Instant feedback  | 100-150ms  |
| State changes     | 200-300ms  |
| Layout changes    | 300-500ms  |
| Entrance anims    | 500-800ms  |

Exit animations: use ~75% of enter duration.

### Easing Curves

```css
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);   /* Smooth, refined */
--ease-out-quint: cubic-bezier(0.22, 1, 0.36, 1);   /* Slightly snappier */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);    /* Confident, decisive */
```

AVOID bounce `(0.34, 1.56, 0.64, 1)` and elastic `(0.68, -0.6, 0.32, 1.6)` -- they feel dated and draw attention to the animation itself.

### Entrance Animations

**Page load choreography:**
- Stagger element reveals (100-150ms delays between each)
- Fade + slide combinations (translateY 20-30px, not 100px)
- Hero section: dramatic entrance for primary content

**Content reveals:**
- Scroll-triggered animations using IntersectionObserver
- Fade in as elements enter viewport

**Modal/drawer entry:**
- Slide + fade entry, backdrop fade
- Focus management on entry
- Smooth reverse on exit (~75% of entry duration)

### Navigation & Flow

- **Page transitions**: Crossfade between routes, shared element transitions via View Transitions API
- **Tab switching**: Slide indicator, content fade or slide in direction of navigation
- **Carousel/slider**: Smooth transforms, snap points, momentum
- **Scroll effects**: Parallax layers, sticky headers with state changes, scroll progress indicators

### Feedback & Guidance

- **Hover hints**: Tooltip fade-ins (not instant), cursor changes, element highlights
- **Drag & drop**: Lift effect (shadow + scale up slightly), drop zone highlights, smooth repositioning on drop
- **Copy/paste**: Brief highlight flash on paste, "Copied!" confirmation that fades
- **Focus flow**: Highlight active step in multi-step forms or workflows

### CSS vs JS Animation Decision

Use CSS for:
- Simple, declarative state changes (transitions)
- Repeating or looping animations (`@keyframes`)
- Anything where `transform` + `opacity` is sufficient

Use JavaScript for:
- Complex interactive animations (drag, physics-based)
- Animations that need to be cancelled, reversed, or composed
- Sequenced choreography across multiple elements

```javascript
// Web Animations API for programmatic control
el.animate([
  { opacity: 0, transform: 'translateY(20px)' },
  { opacity: 1, transform: 'translateY(0)' }
], { duration: 300, easing: 'cubic-bezier(0.25, 1, 0.5, 1)', fill: 'forwards' });

// Framer Motion for React
// GSAP for complex sequences
```

### Common Animation Patterns

- **Page load**: Stagger element reveals (100-150ms delays), fade + slide
- **Modals/drawers**: Slide + fade entry, backdrop fade
- **Buttons**: Hover scale 1.02-1.05, click scale 0.95 then 1
- **Show/hide**: Fade + slide (200-300ms), not instant
- **Expand/collapse**: Height transition with overflow handling, icon rotation
- **Tabs**: Slide indicator, content fade/slide
- **Scroll effects**: Parallax, sticky header state changes, scroll progress

### Performance Rules

- Only animate `transform` and `opacity` (GPU-accelerated)
- Use `will-change` sparingly
- Target 60fps; simplify if below 50
- Lazy-init heavy resources near viewport
- Pause off-screen rendering

### Accessibility (Required)

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### NEVER (Animation)

- Animate layout properties (width, height, top, left) -- use transform
- Use durations over 500ms for feedback
- Animate without purpose
- Ignore `prefers-reduced-motion`
- Animate everything (animation fatigue)
- Block interaction during animations unless intentional

---

## 4. Delight and Personality

### Delight Principles

**Amplifies, never blocks:**
- Delight moments should be quick (< 1 second)
- Never delay core functionality for delight
- Make delight skippable or subtle

**Surprise and discovery:**
- Hide delightful details for users to find, not announce
- Reward curiosity and exploration
- Let users share discoveries with others

**Compound over time:**
- Delight should remain fresh with repeated use
- Vary responses (not same animation every time)
- First-time actions deserve special treatment

### High-Value Delight Moments

- **Success states**: Checkmark draw animation, confetti for milestones, gentle scale + fade
- **Empty states**: Custom illustrations, encouraging copy, subtle floating animations
- **Loading states**: Product-specific messages, skeleton screens, progress with personality
- **Error states**: Empathetic copy, friendly illustrations, recovery paths
- **Hover surprises**: Icons that animate, color shifts, personality in tooltips

### Detailed Micro-interaction Techniques

**Button delight:**
```css
.button {
  transition: transform 0.1s, box-shadow 0.1s;
}
.button:hover {
  transform: translateY(-2px);
  transition: transform 0.2s cubic-bezier(0.25, 1, 0.5, 1);
}
.button:active {
  transform: translateY(2px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
```

**Drag and drop delight:**
- Lift effect on drag start (shadow increase + scale 1.02)
- Snap animation when dropped correctly
- Satisfying placement sound (optional)
- "Dropped in wrong place? [Undo]" toast

**Toggle switches:**
- Smooth slide with spring physics (200-300ms)
- Color transition (gray to brand color)
- Optional haptic feedback on mobile
- Optional subtle sound effect

**Form interactions:**
- Input fields that animate focus (border glow or scale)
- Checkboxes with a satisfying scale pulse when checked
- Auto-grow textareas (no sudden jump)

### Copy Personality

Match tone to brand. Banks can be warm, not wacky. Consumer apps can be playful.

- Error: "Looks like the internet took a coffee break. Want to retry?"
- Empty: "Your canvas awaits. Create something amazing."

**Write product-specific loading messages, not generic AI filler:**
- Good: "Crunching your latest numbers...", "Syncing with your team's changes..."
- Bad: "Herding pixels", "Teaching robots to dance", "Consulting the magic 8-ball" -- these are AI slop copy, instantly recognizable as machine-generated

### Sound Design

When appropriate:
- Notification sounds (distinctive but not annoying)
- Success sounds (satisfying "ding")
- Error sounds (empathetic, not harsh)
- Typing sounds for chat/messaging

**Always**: Respect system sound settings, provide mute option, keep volumes quiet, do not play on every interaction.

### Easter Eggs & Hidden Delights

- Konami code unlocks special theme
- Hidden keyboard shortcuts for power users
- Alt text jokes on images (for screen reader users too)
- Console messages for developers ("Like what you see? We're hiring!")
- Seasonal touches (subtle, tasteful)

### Celebration Moments

**Success celebrations:**
- Confetti for major milestones
- Animated checkmarks for completions
- Progress bar celebrations at 100%
- Personalized messages ("You published your 10th article!")

**Milestone recognition:**
- First-time actions get special treatment
- Streak tracking and celebration
- Anniversary celebrations

### Implementation Libraries

- **Framer Motion**: React animations with spring physics
- **GSAP**: Universal, complex sequences
- **Lottie**: After Effects animations exported to JSON
- **canvas-confetti**: Party effects
- **Howler.js**: Audio management
- **React Spring**: Spring physics for React

### NEVER (Delight)

- Delay core functionality for delight
- Force users through delightful moments
- Use delight to hide poor UX
- Make every interaction delightful (special should be special)
- Sacrifice performance
- Use cliched loading messages ("Herding pixels", "Teaching robots to dance") -- AI slop copy
- Be inappropriate for context (banking app is not a gaming app)

---

## 5. Final Polish Checklist

### Visual Alignment and Spacing

- [ ] Everything aligns to grid, consistent spacing scale
- [ ] Optical alignment adjusted for visual weight (icons may need offset)
- [ ] Responsive: spacing works at all breakpoints

### Typography

- [ ] Hierarchy consistent: same elements use same sizes/weights
- [ ] Body text line length: 45-75 characters
- [ ] No tinted neutrals using pure gray -- add 0.01 chroma

### Interaction States (every interactive element)

- [ ] Default, hover, focus, active, disabled, loading, error, success
- [ ] Focus indicators visible with sufficient contrast
- [ ] Keyboard navigation works, logical tab order

### Transitions

- [ ] All state changes animated (150-300ms)
- [ ] Consistent easing: ease-out-quart/quint/expo
- [ ] 60fps, only transform and opacity
- [ ] Respects `prefers-reduced-motion`

### Content and Copy

- [ ] Consistent terminology and capitalization
- [ ] No typos, appropriate length
- [ ] Punctuation consistency

### Edge Cases

- [ ] Loading states for all async actions
- [ ] Helpful empty states (not blank)
- [ ] Clear error messages with recovery paths
- [ ] Long content handled (truncation, wrapping)
- [ ] No layout shift on load (CLS)

### Responsiveness

- [ ] Mobile, tablet, desktop tested
- [ ] Touch targets 44x44px minimum
- [ ] No text smaller than 14px on mobile
- [ ] No horizontal scroll

### Code Cleanup

- [ ] No console.log, commented code, unused imports
- [ ] No hard-coded colors (use design tokens)
- [ ] Proper ARIA labels and semantic HTML

### NEVER (Polish)

- Polish before it is functionally complete
- Introduce bugs while polishing
- Ignore systematic issues (fix the system, not individual instances)
- Perfect one thing while leaving others rough

---

## 6. Advanced Effects (Overdrive)

For technically ambitious implementations. Always propose 2-3 directions and get user confirmation before building. Skipping the proposal step risks building something that needs to be thrown away.

### CSS-Only Entry Animations with @starting-style

Animate elements from `display: none` to visible with CSS only -- no JavaScript needed:

```css
.modal {
  transition: opacity 0.3s, transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}

@starting-style {
  .modal {
    opacity: 0;
    transform: translateY(20px);
  }
}
```

Supported in all modern browsers.

### @property for Gradient & Color Interpolation

Register custom CSS properties to enable animation of gradients and colors:

```css
@property --gradient-stop-1 {
  syntax: '<color>';
  initial-value: oklch(70% 0.2 250);
  inherits: false;
}

@property --progress {
  syntax: '<percentage>';
  initial-value: 0%;
  inherits: false;
}

.animated-gradient {
  background: linear-gradient(to right, var(--gradient-stop-1), oklch(70% 0.2 180));
  transition: --gradient-stop-1 0.5s;
}

.animated-gradient:hover {
  --gradient-stop-1: oklch(60% 0.3 30);
}
```

### Scroll-Driven Animation

CSS-only scroll progress and reveal effects:

```css
@supports (animation-timeline: scroll()) {
  .progress-bar {
    animation: grow-width linear;
    animation-timeline: scroll();
    animation-range: 0% 100%;
  }

  @keyframes grow-width {
    from { width: 0%; }
    to { width: 100%; }
  }
}
```

Supported in Chrome/Edge/Safari. Always provide a static fallback for Firefox.

**Key techniques by goal:**

- **Cinematic transitions**: View Transitions API, `@starting-style`, spring physics (motion/GSAP)
- **Scroll-driven animation**: `animation-timeline: scroll()` (CSS-only, Chrome/Edge/Safari)
- **Beyond CSS rendering**: WebGL (Three.js, OGL), Canvas 2D, SVG filter chains
- **Data at scale**: Virtual scrolling, GPU-accelerated charts (Canvas/WebGL), animated data transitions
- **Complex property animation**: `@property` for gradient/color interpolation, Web Animations API
- **Performance-critical**: Web Workers, OffscreenCanvas, WASM

**Rules**: Progressive enhancement is non-negotiable. Every technique must degrade gracefully. Always respect `prefers-reduced-motion`. Test on real mid-range devices. Focus creates impact; excess creates noise.
