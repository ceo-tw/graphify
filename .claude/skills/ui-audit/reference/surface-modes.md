# Surface Modes & Design Governance

Classify surfaces by URL route patterns and perform audit/critique with rules matching each surface.

---

## Surface Classification

| Route Pattern | Surface | Example |
|---------------|---------|---------|
| `/(auth)/*` | Auth / Entry | /login, /register, /forgot-password |
| `/(onboarding)/*` | Onboarding | /onboarding, /onboarding/particle-form |
| `/portal/ai-chat`, `/portal/chat*` | Chat / AI Workspace | /portal/ai-chat |
| `/portal/*` (all others) | Portal / Operations | /portal/plans, /portal/dashboard, /portal/settings |
| `/(public)/*` | Auth / Entry (variant) | /privacy, /terms |

---

## Surface Rules

### Auth / Entry
- **Purpose**: Brand-first acquisition and activation surface
- **Composition**: One dominant visual panel, short scannable copy, one primary CTA
- **Allowed expression**: Higher motion, stronger visual contrast, more atmospheric treatment than portal surfaces
- **Rules**: Brand first, promise second, CTA third; no cluttered hero devices
- **Audit focus**: Brand clarity, conversion hierarchy, visual memorability

### Portal / Operations
- **Purpose**: Enterprise management workspace for monitoring, configuration, billing, IAM, and operations
- **Composition**: Navigation + primary workspace + optional secondary context
- **Rules**: Utility-first copy, dense but readable information, minimal chrome, one clear accent for action or state
- **Anti-patterns**: Marketing hero copy, decorative gradients, unnecessary card mosaics
- **Audit focus**: Operational clarity, information density, card restraint

### Chat / AI Workspace
- **Purpose**: Conversation-first operational workspace
- **Composition**: Sidebar/thread context + primary conversation canvas + action composer
- **Rules**: Full-width layouts are allowed only when the workspace itself is the product
- **Anti-patterns**: Framed dashboard treatment around routine chat flows
- **Audit focus**: Conversational rhythm, low chrome, focus

### Onboarding
- **Purpose**: Guided setup and activation flow
- **Composition**: Narrative progression, one dominant task per step, explicit next action
- **Allowed expression**: Higher visual drama and stronger motion than portal surfaces
- **Rules**: Must remain within the same brand family and not introduce an unrelated visual language
- **Audit focus**: Progressive clarity, step completion rate, visual trust

---

## Composition Rules

- **One job per section**: Every section must explain, orient, support, or convert -- never multiple at once
- **Portal pages**: Start with the working surface, not a hero
- **Auth surfaces**: Treat the first viewport as a poster, not a document
- **Width policy**: Constrained layouts by default; full-width reserved for chat, canvas, or immersive workspace flows
- **Hierarchy**: Product or page identity must be readable by scanning title, supporting line, and primary action only

---

## Card & Container Policy

- **Default**: No cards by default
- **Allowed card use**: Widget containers, isolated records, confirmations, or clearly bounded interactions
- **Dashboard exception**: Cards are allowed when the card itself is the draggable/resizable interaction unit
- **Rule**: If a panel can become plain layout without losing meaning, remove the card treatment
- **Anti-pattern**: Routine admin pages made of stacked generic cards instead of layout

---

## Copy Mode

| Surface | Copy Style | Rule |
|---------|-----------|------|
| Portal | Utility copy only | Orientation, status, scope, freshness, action |
| Auth | Brand copy allowed | Must remain short and concrete |
| Onboarding | Instructional, sequential | Never vague or campaign-like |
| Chat | Minimal | System messages only when necessary |

- **Rule**: If a sentence could live in a landing-page hero, it does not belong on a management surface
- **Headings**: Must state what the area is or what the user can do there

---

## Accent & Semantic Color Governance

- **Portal accent policy**: One primary accent by default
- **Semantic reservation**: Success, warning, error, inactive, trend, and destructive colors are reserved for meaning, not decoration
- **Vendor/category colors**: Allowed only when the distinction is operationally useful and consistently applied
- **Rule**: Accent color must not compete with semantic status colors
- **Anti-pattern**: Multiple unrelated accent colors within a single admin surface

---

## Motion & Imagery Policy

| Surface | Motion Budget | Rule |
|---------|--------------|------|
| Portal | Functional only | Drawers, menus, loading transitions, layout state changes |
| Auth / Onboarding | 2-3 intentional motions max | Must improve hierarchy or presence |
| Chat | Minimal | Message transitions, typing indicators |

- **Imagery**: Real-looking persona imagery or clear narrative visuals only
- **Rule**: Decorative gradients or abstract effects should not carry meaning on routine product UI
- **Anti-pattern**: Motion or imagery that feels campaign-like inside dense operational screens

---

## Audit Litmus Checks

When auditing any page, run these checks after classifying the surface:

- [ ] **Brand clarity**: Is the product identity unmistakable on entry surfaces?
- [ ] **Operational clarity**: Can an operator understand the page by scanning headings, labels, and numbers only?
- [ ] **Composition**: Does each section have one dominant job and one dominant visual idea?
- [ ] **Card restraint**: Are cards actually necessary here?
- [ ] **Accent discipline**: Is color being used semantically rather than decoratively?
- [ ] **Motion discipline**: Does motion sharpen hierarchy, or is it just ornament?
- [ ] **Surface consistency**: Does this screen belong to the same product family as the rest of the system?
