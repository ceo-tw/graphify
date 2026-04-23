# Content Fix Reference

Fixes for UX writing, microcopy, onboarding, and content clarity issues.

---

## 1. UX Writing

### Find Clarity Problems First

Before rewriting, assess what's actually broken. Look for:

- **Jargon**: Technical terms users won't understand
- **Ambiguity**: Multiple interpretations possible
- **Passive voice**: "Your file has been uploaded" vs "We uploaded your file"
- **Length**: Too wordy or too terse
- **Assumptions**: Assuming user knowledge they don't have
- **Missing context**: Users don't know what to do or why
- **Tone mismatch**: Too formal, too casual, or inappropriate for the situation

### Error Messages
**Bad** -> **Good**:
- "Error 403: Forbidden" -> "You don't have permission to view this page. Contact your admin for access."
- "Invalid input" -> "Email addresses need an @ symbol. Try: name@example.com"

**Rules**: Explain what went wrong in plain language. Suggest how to fix it. Don't blame the user. Include examples when helpful. Link to help/support if applicable.

### Form Labels & Instructions
**Bad** -> **Good**:
- "DOB (MM/DD/YYYY)" -> "Date of birth" (with placeholder showing format)
- "Enter value here" -> "Your email address" or "Company name"

**Rules**: Use clear, specific labels. Show format expectations with examples. Explain why you're asking (when not obvious). Put instructions before the field. Never use placeholders as the only labels (they disappear when users type).

### Buttons & CTAs
**Bad** -> **Good**:
- "Click here" / "Submit" / "OK" -> "Create account" / "Save changes" / "Got it, thanks"

**Rules**: Describe the action specifically. Use active voice (verb + noun). Match user's mental model. Be specific ("Save" is better than "OK").

### Help Text & Tooltips
**Bad** -> **Good**:
- "This is the username field" -> "Choose a username. You can change this later in Settings."

**Rules**: Add value beyond the label. Answer "What is this?" or "Why do you need this?". Keep brief but complete. Link to detailed docs if needed.

### Empty States
**Bad** -> **Good**:
- "No items" -> "No projects yet. Create your first project to get started."

**Rules**: Explain why it's empty. Show next action clearly. Make it welcoming, not dead-end.

### Success Messages
**Bad** -> **Good**:
- "Success" -> "Settings saved! Your changes will take effect immediately."

**Rules**: Confirm what happened. Explain what happens next. Match the user's emotional moment (celebrate big wins).

### Loading States
**Bad** -> **Good**:
- "Loading..." (30+ sec) -> "Analyzing your data... this usually takes 30-60 seconds"

**Rules**: Set expectations (how long?). Explain what's happening when not obvious. Show progress when possible. Offer escape hatch ("Cancel").

### Confirmation Dialogs

**Bad** -> **Good**:
- "Are you sure?" -> "Delete 'Project Alpha'? This can't be undone."

**When to use confirmation dialogs:**
- Destructive actions that cannot be undone (delete, remove, revoke)
- Actions with significant consequences (publish, send to all users)
- Actions that are easy to trigger accidentally

**When NOT to use:**
- Routine actions (save, update settings, create)
- Actions that are easily reversible
- Anything users do repeatedly (confirmation fatigue is real)

**Confirmation dialog copy rules:**
- State the specific action ("Delete 'Project Alpha'?" not "Are you sure?")
- Explain consequences ("This can't be undone", "All members will lose access")
- Use clear button labels ("Delete project" not "Yes"; "Keep project" not "No" or "Cancel")
- Make the destructive button clearly destructive (red color, specific label)

### Navigation & Wayfinding

**Bad** -> **Good**:
- "Items" / "Things" / "Stuff" -> "Your projects" / "Team members" / "Settings"

**Rules:**
- Be specific and descriptive -- use language users understand, not internal jargon
- Make hierarchy clear through label specificity
- Consider information scent: breadcrumbs, active states, and page titles should tell users where they are
- Active nav items: show current location clearly
- Page titles: match the nav label users clicked to get here

**Breadcrumb patterns:**
```
Home > Projects > Project Alpha > Settings
```
- Use " > " or "/" separator
- Last item (current page) should not be a link
- All parent items should be links

---

## 2. Onboarding

### Onboarding Principles

**Show, Don't Tell:**
- Demonstrate with working examples, not just descriptions
- Provide real functionality in onboarding, not a separate tutorial mode
- Use progressive disclosure -- teach one thing at a time

**Make It Optional (When Possible):**
- Let experienced users skip onboarding
- Don't block access to the product
- Provide "Skip" or "I'll explore on my own" options prominently

**Time to Value:**
- Get users to their "aha moment" as quickly as possible
- Front-load the 20% that delivers 80% of value
- Save advanced features for contextual discovery later

**Context Over Ceremony:**
- Teach features when users encounter them, not upfront
- Empty states are onboarding opportunities
- Tooltips and hints at the point of use are more effective than tours

**Respect User Intelligence:**
- Don't patronize or over-explain
- Be concise and clear
- Assume users can figure out standard patterns

### Initial Product Onboarding

**Welcome Screen:**
- Clear value proposition (what is this product?)
- What users will accomplish with it
- Time estimate (honest about commitment)
- Option to skip (for experienced users)

**Account Setup:**
- Minimal required information (collect more later)
- Explain why you're asking for each piece of information
- Smart defaults where possible
- Social login when appropriate

**Core Concept Introduction:**
- Introduce 1-3 core concepts (not everything)
- Use simple language and examples
- Interactive when possible (do, don't just read)
- Progress indication ("Step 1 of 3")

**First Success:**
- Guide users to accomplish something real
- Pre-populated examples or templates to start from
- Celebrate completion (but don't overdo it)
- Clear next steps after completion

### Feature Discovery & Adoption

**Contextual Tooltips:**
- Appear at the relevant moment (first time user sees a feature)
- Point directly at the relevant UI element
- Brief explanation + the benefit ("See how your team is using this")
- Dismissable with "Don't show again" option
- Optional "Learn more" link for deeper reading

**Feature Announcements:**
- Highlight new features when they're released
- Show what's new and why it matters
- Let users try immediately from the announcement
- Dismissable

**Progressive Onboarding:**
- Teach features when users encounter them
- Badges or indicators on new/unused features
- Unlock complexity gradually -- don't show all options immediately

### Guided Tours & Walkthroughs

**When to use:**
- Complex interfaces with many features
- Significant changes to an existing product
- Industry-specific tools needing domain knowledge

**How to design:**
- Spotlight specific UI elements (dim rest of page)
- Keep steps short (3-7 steps max per tour)
- Allow users to click through the tour themselves
- Include "Skip tour" option prominently
- Make replayable from a help menu

**Best practices:**
- Interactive > passive -- let users click real buttons, not observe
- Focus on workflow ("Create a project") not features ("This is the project button")
- Provide sample data so user actions actually work
- Don't lock all UI during the tour -- let users explore

### Interactive Tutorials

**When to use:**
- Users need hands-on practice
- Concepts are complex or unfamiliar
- High stakes (better to practice in a safe environment)

**How to design:**
- Sandbox environment with sample data
- Clear objectives ("Create a chart showing sales by region")
- Step-by-step guidance with validation
- Confirm they did it right before moving on
- Graduation moment ("You're ready!")

### Documentation & Help Patterns

- Contextual help links (`?` icon near complex features)
- "Learn more" links in tooltips
- Keyboard shortcut hints (`Cmd+K` shown on search box)
- Keyboard shortcut reference page (accessible at any time)
- Search-able help center
- Video tutorials for complex workflows

### Empty State Design (5 elements)
Every empty state needs:
1. **What will be here**: "Your recent projects will appear here"
2. **Why it matters**: "Projects help you organize your work"
3. **How to get started**: [Create project] or [Import from template]
4. **Visual interest**: Illustration or icon (not just text on blank page)
5. **Contextual help**: "Need help? [Watch 2-min tutorial]"

### Empty State Types
| Type | Approach |
|------|----------|
| First use | Emphasize value, provide template |
| User cleared | Light touch, easy to recreate |
| No results | Suggest different query, clear filters |
| No permissions | Explain why, how to get access |
| Error state | Explain what happened, retry option |

### Implementation Patterns

**Tooltip libraries**: Tippy.js, Popper.js
**Tour libraries**: Intro.js, Shepherd.js, React Joyride
**Progress tracking**: LocalStorage for "seen" states

```javascript
// Track which onboarding steps user has seen
localStorage.setItem('onboarding-completed', 'true');
localStorage.setItem('feature-tooltip-seen-reports', 'true');
```

**Analytics to track**: Completion rate, drop-off points, skip rate, time to first value

---

## 3. Clarity Principles

Every piece of copy must follow:

1. **Be specific**: "Enter email" not "Enter value"
2. **Be concise**: Cut unnecessary words without sacrificing clarity
3. **Be active**: "Save changes" not "Changes will be saved"
4. **Be human**: "Oops, something went wrong" not "System error encountered"
5. **Be helpful**: Tell users what to do, not just what happened
6. **Be consistent**: Use same terms throughout (don't vary for variety)

### NEVER
- Use jargon without explanation
- Blame users ("You made an error" -> "This field is required")
- Be vague ("Something went wrong" without context)
- Use passive voice unnecessarily
- Write overly long explanations
- Assume technical knowledge
- Vary terminology (pick one term, stick with it)
- Repeat information across headers and body
- Force users through long onboarding before they can use product
- Show same tooltip repeatedly (track and respect dismissals)
- Block all UI during tours
- Create separate tutorial modes disconnected from real product
- Hide "Skip" options

### Verification Checklist
- [ ] Comprehension: Can users understand without context?
- [ ] Actionability: Do users know what to do next?
- [ ] Brevity: Is it as short as possible while remaining clear?
- [ ] Consistency: Does it match terminology elsewhere?
- [ ] Tone: Is it appropriate for the situation?
