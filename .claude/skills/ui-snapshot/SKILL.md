---
name: ui-snapshot
description: >
  Collects and snapshots the current project's design system into .ui-snapshot.md.
  Automatically extracts: shadcn/ui config, CSS variables/tokens, component inventory,
  font system, color palette, spacing scale, and icon library from the codebase.
  Optionally gathers brand/audience context from the user.
  Use this skill when: starting UI work for the first time, before running /ui audit,
  the design system has changed, or someone asks about the project's design tokens,
  components, or visual foundation. Also triggers on: 디자인 시스템 수집, UI 스냅샷,
  컴포넌트 목록, 디자인 토큰 확인, 프로젝트 디자인 파악.
user-invocable: true
argument-hint: "[src/admin-portal] [--with-context]"
---

Snapshot the project's design system by extracting concrete facts from the codebase,
then optionally gather subjective brand/audience context from the user.

The output file `.ui-snapshot.md` serves as the single source of truth that `/ui` reads
before auditing -- so every audit compares against *this project's actual standards*,
not generic best practices.

---

## When to Run

- **First time**: Before the very first `/ui` invocation (no `.ui-snapshot.md` exists)
- **After design changes**: When globals.css, components.json, or the component library changes
- **Manually**: When the user wants to review or refresh the design system snapshot

---

## Step A: Design System Extraction (Automatic)

Scan the target service directory (default: `src/admin-portal/`) and extract the following.
All data comes from reading files -- no user input required.
All sub-steps (A1-A5) are independent reads and can be executed in parallel.

### A1. Framework & Config

Read `components.json` (shadcn/ui config):

```
- Style variant (e.g., new-york)
- Base color (e.g., neutral)
- CSS variables enabled? (true/false)
- Icon library (e.g., lucide)
- Alias paths (components, ui, lib, hooks, utils)
```

Read `package.json` for UI-relevant dependencies:

```
- Component framework (react version)
- CSS framework (tailwindcss version)
- Animation library (motion, framer-motion, gsap)
- Chart library (recharts, chart.js, d3)
- Table library (@tanstack/react-table)
- Icon library (lucide-react)
- Theme library (next-themes)
- Toast library (sonner, react-hot-toast)
- Form library (react-hook-form, @hookform/resolvers, zod)
- Other UI deps (cmdk, vaul, @radix-ui/*)
```

### A2. Design Tokens (CSS Variables)

Read `globals.css` (or the CSS file referenced in components.json `tailwind.css`):

**Color tokens** -- extract all `--` custom properties from `:root` and `.dark`:

| Category | Token Pattern | Example |
|----------|--------------|---------|
| Core | `--background`, `--foreground`, `--card`, `--popover` | #F7F5F0 |
| Brand | `--primary`, `--secondary`, `--accent` | #FF4D4D |
| Semantic | `--destructive`, `--success`, `--warning`, `--info` | #0099A0 |
| Status | `--status-running`, `--status-error`, `--status-awaiting` | #00A86B |
| Chart | `--chart-1` through `--chart-N` | oklch(...) |
| Sidebar | `--sidebar`, `--sidebar-primary`, `--sidebar-accent` | #F7F5F0 |
| Domain-specific | `--log-*`, `--k8s-*`, `--chat-*`, `--avatar-*`, `--code-*`, `--trend-*` | varies |

**Non-color tokens**:

| Category | Token Pattern | Example |
|----------|--------------|---------|
| Font families | `--font-sans`, `--font-mono`, `--font-serif` | "Geist", sans-serif |
| Border radius | `--radius` | 0.375rem |
| Shadows | `--shadow-2xs` through `--shadow-2xl` | rgba(...) |

**Dark mode**: List all tokens that change between `:root` and `.dark`, noting the differences.

### A3. Component Inventory

List all files in `components/ui/` directory:

```
Format: component-name (from filename without .tsx)
Group by category:
  - Layout: card, separator, scroll-area, collapsible, sidebar
  - Form: input, textarea, select, checkbox, radio-group, switch, label, form, input-group
  - Feedback: alert, alert-dialog, dialog, drawer, sheet, tooltip, hover-card, popover, toast
  - Navigation: tabs, breadcrumb, command, context-menu, dropdown-menu, button-group
  - Data: table, badge, avatar, progress, skeleton, spinner, chart, timeline
  - Action: button, accordion, carousel
  - Utility: motion-preset
```

Also scan `components/common/` for shared custom components (StatusBadge, ConfirmDialog, EmptyState, etc.).

### A4. Tailwind v4 Theme

Read the `@theme inline` block from globals.css to extract:
- Which CSS variables are mapped to Tailwind colors
- Custom keyframes and animations
- Custom utilities (`@utility`)

### A5. Layout Patterns

Scan for common layout patterns by checking:
- `app/portal/layout.tsx` -- main portal layout structure (sidebar? top nav?)
- Responsive breakpoints used (grep for `md:`, `lg:`, `xl:` in components)
- Grid patterns (`grid-cols-`, `grid-template`)

---

## Step B: Brand & Audience Context (Interactive, Optional)

This step only runs when:
- `--with-context` flag is passed, OR
- No `.impeccable.md` exists at project root

Ask the user focused questions using AskUserQuestion:

### B1. Target Audience
- Who uses this product? (e.g., SaaS admin operators, developers, business analysts)
- What's their technical level? (beginner / intermediate / advanced)
- What's the usage context? (desktop-focused? mobile too? internal tool?)

### B2. Brand Personality
- 3 words that describe the desired feel (e.g., "professional, warm, efficient")
- Any reference products or sites that capture the right aesthetic?
- What should it explicitly NOT look like?

### B3. Design Priorities
- What matters most? (consistency > creativity? accessibility > aesthetics?)
- Known pain points in current UI?

Write the answers to the `## Brand Context` section of `.ui-snapshot.md`.

---

## Output: `.ui-snapshot.md`

Write the file to the project root. Use this exact structure:

```markdown
# UI Design System Snapshot

> Generated: {date}
> Service: {service path}
> Auto-regenerate: `/ui-snapshot {service path}`

## Framework
- **Component library**: shadcn/ui ({style} style)
- **CSS**: Tailwind CSS v{version} (v4 with @theme inline)
- **React**: v{version}
- **Icons**: {library} ({count} available)
- **Theme**: {library} (light/dark)

## Color Palette

### Light Mode
| Token | Value | Usage |
|-------|-------|-------|
| --primary | #FF4D4D | Brand accent, CTAs |
| --background | #F7F5F0 | Page background |
| ... | ... | ... |

### Dark Mode Overrides
| Token | Light | Dark |
|-------|-------|------|
| --background | #F7F5F0 | #000000 |
| ... | ... | ... |

### Semantic Colors
| Purpose | Token | Light | Dark |
|---------|-------|-------|------|
| Success | --success / --status-running | #00A86B | (same) |
| Error | --destructive / --status-error | #0099A0 / #A73000 | #50D3C4 |
| Warning | --warning / --status-awaiting | #C4A000 / #B39500 | (same) |
| Info | --info | #007ACC | (same) |

### Chart Colors
| Token | Value |
|-------|-------|
| --chart-1 | oklch(...) |
| ... | ... |

### Domain Colors
| Domain | Tokens |
|--------|--------|
| Log viewer | --log-bg, --log-error, --log-warn, --log-info, --log-debug |
| K8s status | --k8s-running, --k8s-pending, --k8s-failed |
| Chat | --chat-user-bubble, --chat-agent-bubble |
| Avatar roles | --avatar-ceo (#4F46E5), --avatar-cto (#7C3AED), ... |
| Code blocks | --code-bg, --code-foreground, --code-border |
| Trends | --trend-up (#00A86B), --trend-down (#A73000) |

## Typography
- **Sans**: {font} (variable, {weights})
- **Mono**: {font} (variable, {weights})
- **Serif**: {fallback stack}
- **Loading**: font-display: swap

## Spacing & Radius
- **Border radius**: {value}
- **Shadow scale**: {count} levels ({list})

## Component Inventory

### shadcn/ui ({count} components)
| Category | Components |
|----------|-----------|
| Layout | card, separator, scroll-area, ... |
| Form | input, textarea, select, ... |
| ... | ... |

### Custom Shared Components
| Component | Path | Purpose |
|-----------|------|---------|
| StatusBadge | components/common/ | Status indicator |
| ... | ... | ... |

## UI Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| recharts | x.x.x | Charts |
| @tanstack/react-table | x.x.x | Data tables |
| motion | x.x.x | Animations |
| sonner | x.x.x | Toast notifications |
| ... | ... | ... |

## Layout Patterns
- **Portal layout**: {description}
- **Responsive**: {breakpoints used}
- **Grid patterns**: {common patterns}

## Brand Context
{only if Step B was run}
- **Audience**: {who, technical level, context}
- **Personality**: {3 words}
- **References**: {sites/products}
- **Anti-references**: {what to avoid}
- **Priorities**: {what matters most}
```

---

## Integration with `/ui`

After `.ui-snapshot.md` is generated, the `/ui` skill's Step 0 should:

1. Check for `.ui-snapshot.md` at project root
2. If found, load it as the project's design baseline
3. Use it to calibrate audit scoring:
   - "Hard-coded color" = color NOT in the snapshot's token list
   - "Off-pattern component" = custom component where a shadcn equivalent exists
   - "Inconsistent spacing" = spacing not in the project's scale
4. If not found, suggest running `/ui-snapshot` first

This ensures audits compare against the project's actual design system, not generic rules.

---

## Maintenance

The snapshot should be regenerated when:
- New shadcn/ui components are added (`npx shadcn@latest add`)
- `globals.css` color tokens are modified
- Major dependency upgrades (React, Tailwind, etc.)
- Brand direction changes

Add `.ui-snapshot.md` to `.gitignore` if it should be machine-local, or commit it if the team should share the same baseline.
