# Technical Fix Reference

Actionable techniques for design system normalization, UI hardening, and performance optimization.

---

## 1. Design System Normalization

### Prerequisite: Discover the Design System First

Before making any changes, thoroughly understand the design system in place:

- Search for design system documentation, UI guidelines, component libraries, and style guides (grep for "design system", "ui guide", "style guide", etc.)
- Study core design principles and aesthetic direction
- Understand target audience and personas
- Learn component patterns, conventions, and design tokens (colors, typography, spacing)

**CRITICAL**: If something isn't clear, ask. Do not guess at design system principles.

### Token Alignment

- **Typography**: Replace hard-coded font sizes, weights, and line heights with design system tokens/classes.
- **Color & Theme**: Use design system color tokens. Remove one-off color values that break the palette.
- **Spacing & Layout**: Use spacing tokens for margins, padding, gaps. Align with established grid systems.

### 8-Dimension Systematic Check

Work through each dimension in order:

1. **Typography**: Use design system fonts, sizes, weights, and line heights. Replace hard-coded values with typographic tokens or classes.
2. **Color & Theme**: Apply design system color tokens. Remove one-off color choices that break the palette.
3. **Spacing & Layout**: Use spacing tokens (margins, padding, gaps). Align with grid systems and layout patterns used elsewhere.
4. **Components**: Replace custom implementations with design system components. Ensure props and variants match established patterns.
5. **Motion & Interaction**: Match animation timing, easing, and interaction patterns to other features.
6. **Responsive Behavior**: Ensure breakpoints and responsive patterns align with design system standards.
7. **Accessibility**: Verify contrast ratios, focus states, ARIA labels match design system requirements.
8. **Progressive Disclosure**: Match information hierarchy and complexity management to established patterns.

### Component Replacement

- Replace custom implementations with design system equivalents when they exist.
- Ensure props and variants match established component patterns.
- If new shared components are created, move them to the design system or shared UI path.

### Motion & Interaction Matching

- Match animation timing, easing, and interaction patterns to existing features.
- Ensure responsive breakpoints align with design system standards.
- Verify contrast ratios, focus states, and ARIA labels match system requirements.

### Code Cleanup

- Remove orphaned code, styles, or files made obsolete by normalization.
- Consolidate duplication introduced during refactoring (DRY).
- Lint, type-check, and test to ensure no regressions.

### NEVER (Normalization)

- Create new one-off components when design system equivalents exist
- Hard-code values that should use design tokens
- Introduce new patterns that diverge from the design system
- Compromise accessibility for visual consistency

---

## 2. Hardening

### Text Overflow & Truncation

**Single line with ellipsis:**
```css
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

**Multi-line clamp:**
```css
.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

**Word wrapping:**
```css
.wrap {
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
```

**Flex/Grid overflow prevention:**
```css
.flex-item {
  min-width: 0; /* Allow shrinking below content size */
  overflow: hidden;
}
.grid-item {
  min-width: 0;
  min-height: 0;
}
```

**Responsive text**: Use `clamp()` for fluid typography. Set minimum readable size (14px mobile). Test at 200% zoom.

### Internationalization (i18n) & RTL

- Budget 30-40% extra space for translations (German is ~30% longer than English).
- Use flexbox/grid that adapts to content. Avoid fixed widths on text containers.

```jsx
// Bad: Assumes short English text
<button className="w-24">Submit</button>
// Good: Adapts to content
<button className="px-4 py-2">Submit</button>
```

**RTL support -- use logical properties:**
```css
margin-inline-start: 1rem;   /* Not margin-left */
padding-inline: 1rem;        /* Not padding-left/right */
border-inline-end: 1px solid; /* Not border-right */
[dir="rtl"] .arrow { transform: scaleX(-1); }
```

**Character set support:**
- Use UTF-8 encoding everywhere
- Test with Chinese/Japanese/Korean (CJK) characters
- Test with emoji (they can be 2-4 bytes)
- Handle different scripts (Latin, Cyrillic, Arabic, etc.)

**Date/Number formatting -- use Intl API:**
```javascript
new Intl.DateTimeFormat('en-US').format(date);  // 1/15/2024
new Intl.DateTimeFormat('de-DE').format(date);  // 15.1.2024
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(1234.56);
```

**Pluralization:**
```javascript
// Bad: Assumes English pluralization
`${count} item${count !== 1 ? 's' : ''}`

// Good: Use proper i18n library
t('items', { count }) // Handles complex plural rules for all languages
```

### Error Handling

**Network errors**: Show clear message + retry button + explain what happened. Handle timeout.

**API error status codes**:
- 400: Show validation errors inline
- 401: Redirect to login
- 403: Show permission error
- 404: Show not-found state
- 429: Show rate limit message
- 500: Generic error + offer support contact

**Form validation**: Inline errors near fields, specific messages, preserve input on error.

### Edge Cases

**Empty states**: No items, no results, no data -- always provide a clear next action.

**Loading states**: Initial load, pagination, refresh -- describe what is loading, estimate time for long ops.

**Concurrent operations**: Disable submit button while loading, handle race conditions, optimistic updates with rollback.

**Large datasets**: Pagination or virtual scrolling. Never load all items at once.

**Permission states**: No-view, no-edit, read-only -- explain why.

### Input Validation

- Client-side: required, format, length, pattern, custom rules.
- Server-side always (never trust client-side alone).

```html
<input type="text" maxlength="100" pattern="[A-Za-z0-9]+"
  required aria-describedby="hint" />
<small id="hint">Letters and numbers only, up to 100 characters</small>
```

### Accessibility Resilience

- All functionality accessible via keyboard. Logical tab order. Focus management in modals.
- Proper ARIA labels. Announce dynamic changes via live regions. Semantic HTML.

**Motion sensitivity:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- Test in Windows high contrast mode. Never rely only on color for meaning.

### Browser Compatibility

- Polyfills for modern features where needed
- Fallbacks for unsupported CSS (use `@supports`)
- Feature detection, not browser detection
- Test in target browsers (Safari, Chrome, Firefox, Edge)

### Performance Resilience

**Slow connections:**
- Progressive image loading
- Skeleton screens
- Optimistic UI updates
- Service workers for offline support

**Memory leaks:**
- Clean up event listeners on unmount
- Cancel subscriptions and clear timers
- Abort pending fetch requests on unmount

**Throttling & debouncing:**
```javascript
const debouncedSearch = debounce(handleSearch, 300);
const throttledScroll = throttle(handleScroll, 100);
```

### NEVER (Hardening)

- Assume perfect input (validate everything)
- Leave error messages generic ("Error occurred")
- Forget offline scenarios
- Trust client-side validation alone
- Use fixed widths for text containers
- Assume English-length text
- Block entire interface when one component errors

### Hardening Verification Checklist

- [ ] Long text (100+ chars) in all text fields
- [ ] Emoji in all text inputs
- [ ] RTL text (Arabic/Hebrew)
- [ ] CJK characters (Chinese/Japanese/Korean)
- [ ] Network disabled / throttled to 3G
- [ ] 1000+ items in lists
- [ ] Rapid repeated submit (10x)
- [ ] Force API errors on all endpoints
- [ ] All empty states rendered

### Testing Strategies Appendix

**Manual testing priorities:**
- Extreme data (very long, very short, empty)
- Different languages (especially German for length)
- Offline and throttled to 3G
- Screen reader (NVDA, VoiceOver)
- Keyboard-only navigation
- Old browsers

**Automated testing:**
- Unit tests for edge cases and validation
- Integration tests for error scenarios
- E2E tests for critical user paths
- Accessibility tests (axe, WAVE)
- Visual regression tests

---

## 3. Performance Optimization

### Image Optimization

- Use modern formats (WebP, AVIF). Compress at 80-85% quality.
- Proper sizing (do not load 3000px image for 300px display).
- Lazy load below-fold images. Use responsive `srcset` + `sizes`.

```html
<img src="hero.webp"
  srcset="hero-400.webp 400w, hero-800.webp 800w, hero-1200.webp 1200w"
  sizes="(max-width: 400px) 400px, (max-width: 800px) 800px, 1200px"
  loading="lazy" alt="Hero image" />
```

### Bundle Reduction

- Code splitting: route-based and component-based.
- Tree shaking. Remove unused dependencies.
- Lazy load non-critical code with dynamic imports.
- Optimize fonts: `font-display: swap`, subset to needed characters, limit weights.

```javascript
const HeavyChart = lazy(() => import('./HeavyChart'));
```

```css
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0020-007F;
}
```

### CSS Optimization

- Remove unused CSS (PurgeCSS, built-in Tailwind purge)
- Inline critical CSS, load rest asynchronously
- Minimize CSS files
- Use CSS containment for independent regions:

```css
.card {
  contain: layout style paint; /* Isolates rendering */
}
```

### Rendering Performance

- Avoid layout thrashing (batch reads then batch writes):

```javascript
// Bad: Alternating reads and writes
elements.forEach(el => {
  const height = el.offsetHeight; // Read (forces layout)
  el.style.height = height * 2;   // Write
});

// Good: Batch reads, then batch writes
const heights = elements.map(el => el.offsetHeight);
elements.forEach((el, i) => {
  el.style.height = heights[i] * 2;
});
```

- Use CSS `contain` for independent regions.
- Use `content-visibility: auto` for long lists.
- Virtual scrolling for very long lists (react-window, react-virtualized).
- Minimize DOM depth and element count.

### Animation Performance

**GPU-accelerated (fast):** `transform`, `opacity`
**CPU-bound (slow):** `left`, `top`, `width`, `height`

```css
/* Good */
.animated { transform: translateX(100px); opacity: 0.5; }
/* Bad */
.animated { left: 100px; width: 300px; }
```

- Target 16ms per frame (60fps). Use `requestAnimationFrame` for JS animations.
- Use CSS animations over JS when possible. Debounce/throttle scroll handlers.
- Use `will-change` sparingly (creates layers, uses memory).

### Network Optimization

**Reduce requests:**
- Combine small files
- Use SVG sprites for icons
- Inline small critical assets
- Remove unused third-party scripts

**Optimize for slow connections:**
- Adaptive loading based on connection speed (`navigator.connection`)
- Optimistic UI updates
- Request prioritization
- Progressive enhancement

```javascript
// Adaptive loading example
if (navigator.connection?.effectiveType === '4g') {
  loadHighResImages();
} else {
  loadLowResImages();
}
```

### Core Web Vitals Targets

**LCP < 2.5s**: Optimize hero images, inline critical CSS, preload key resources, use CDN, SSR.

```html
<!-- Preload critical resources -->
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin />
<link rel="preload" href="/hero.webp" as="image" />
```

**INP < 200ms**: Break up long tasks, defer non-critical JS, use web workers, reduce JS execution time.

**CLS < 0.1**: Set dimensions on images/video, use `aspect-ratio`, reserve space for dynamic content, never inject content above existing content.

```css
.image-container { aspect-ratio: 16 / 9; }
```

### React-Specific Optimizations

- `React.memo()` for expensive pure components.
- `useMemo()` for expensive computations, `useCallback()` for stable function references.
- Code split routes. Lazy load heavy components.
- Avoid inline function creation in render.
- Virtualize long lists.
- Profile with React DevTools Profiler.

### Resource Cleanup

- Clean up event listeners, cancel subscriptions, clear timers on unmount.
- Abort pending fetch requests on unmount.
- Debounce search inputs (~300ms), throttle scroll handlers (~100ms).

### Performance Monitoring Tools

- **Chrome DevTools**: Lighthouse, Performance panel, Coverage panel for unused CSS/JS
- **WebPageTest**: Real-world testing across devices and locations
- **webpack-bundle-analyzer**: Visualize bundle composition
- **Sentry / DataDog / New Relic**: Real user monitoring (RUM)
- **Chrome UX Report (CrUX)**: Field data on real users

**Key metrics to track:**
- LCP, INP, CLS (Core Web Vitals)
- Time to Interactive (TTI)
- First Contentful Paint (FCP)
- Total Blocking Time (TBT)
- Bundle size and request count

### NEVER (Performance)

- Optimize without measuring first (premature optimization)
- Sacrifice accessibility for performance
- Use `will-change` everywhere
- Lazy load above-fold content
- Ignore mobile performance (slower devices, slower connections)
- Micro-optimize while ignoring major bottlenecks

### Performance Verification

- Compare before/after Lighthouse scores
- Test on low-end Android, not just flagship devices
- Throttle to 3G and verify usability
- Confirm no functional regressions
- Monitor real user metrics (CrUX, RUM)
