# Problem Solving Methods Reference

This document provides detailed guidance on the methodologies used in the /solve skill.

---

## 5 Whys Methodology

### Overview

The 5 Whys is a root cause analysis technique that involves asking "Why?" five times (or more) to drill down from a symptom to its underlying root cause.

### When to Use

- Bug with unclear cause
- Recurring issues
- Complex multi-factor problems
- Post-incident analysis

### Process

| Level | Question | Answer |
|-------|----------|--------|
| **Symptom** | What is happening? | {Observable problem} |
| **Why 1** | Why? | {Direct cause} |
| **Why 2** | Why does Cause 1 exist? | {Deeper cause} |
| **Why 3** | Why does Cause 2 exist? | {Even deeper} |
| **Why 4** | Why does Cause 3 exist? | {Structural issue} |
| **Why 5** | Why does Cause 4 exist? | **ROOT CAUSE** |

### Guidelines

1. **Start with the symptom**: Begin with a clear, specific problem statement
2. **Ask "Why?" iteratively**: Each answer becomes the basis for the next question
3. **Stop when actionable**: Continue until you reach a cause you can directly address
4. **Support with evidence**: Each answer should be backed by data, logs, or code analysis
5. **Don't stop too early**: Often the first 2-3 causes are symptoms, not root causes

### Example

```
Problem: API returns 500 error on user creation

Why 1: Why does the API return 500?
→ Database insert fails

Why 2: Why does the database insert fail?
→ Unique constraint violation on email

Why 3: Why is there a constraint violation?
→ Email already exists in database

Why 4: Why is duplicate email being submitted?
→ No frontend validation before submission

Why 5: Why is there no frontend validation?
→ Email validation was removed during refactoring

ROOT CAUSE: Email validation logic was accidentally removed in commit abc123
```

### Anti-patterns to Avoid

| Anti-pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Blaming people | "Developer made mistake" | Focus on process/system issues |
| Stopping too early | "Bug in the code" | Dig deeper into why bug exists |
| Multiple branches | Following many paths simultaneously | Focus on one path, then explore others |
| Speculation | Guessing without evidence | Support each answer with data |

---

## Hypothesis-Driven Debugging

### Overview

Hypothesis-driven debugging applies the scientific method to problem-solving:

1. Observe the problem
2. Form hypotheses
3. Design experiments
4. Test and verify
5. Accept or reject

### When to Use

- Intermittent or hard-to-reproduce issues
- Multiple possible causes
- Performance problems
- Complex system interactions
- When 5 Whys produces unclear results

### Hypothesis Format

```
Hypothesis #N (Likelihood: High/Medium/Low)

Statement: "{X} is causing {symptom}"

Prediction: "If {X} is the cause, then {Y} should happen when we {action}"

Test Method:
1. {Step 1}
2. {Step 2}
3. {Step 3}

Expected Result: {what we expect if hypothesis is correct}

Status: [ ] Pending / [x] Confirmed / [ ] Rejected

Evidence: {actual test results}
```

### Process

1. **Observe Problem** - Document symptoms and context
2. **Form Hypothesis** - State: "{X} is causing {symptom}"
3. **Design Test** - Create falsifiable experiment
4. **Execute Test** - Run experiment, collect data
5. **Evaluate** - Confirmed? → Implement Fix / Rejected? → Return to step 2

### Guidelines

1. **Rank hypotheses by likelihood**: Start with most likely cause
2. **Design falsifiable tests**: Test should definitively confirm or reject
3. **Change one variable at a time**: Isolate variables for clear results
4. **Document everything**: Record all tests and results
5. **Be willing to be wrong**: Rejected hypotheses are still valuable data

### Example

```
Problem: Tests fail intermittently in CI

Hypothesis 1 (Likelihood: High)
Statement: Race condition in async test
Prediction: Adding explicit wait will make test consistently pass
Test: Add await for async operation
Result: CONFIRMED - Test now passes consistently

Hypothesis 2 (Likelihood: Medium)
Statement: CI resource contention
Prediction: Running test alone will pass consistently
Test: Isolate test in separate CI job
Result: REJECTED - Still fails when isolated

Hypothesis 3 (Likelihood: Low)
Statement: Timezone-related issue
Prediction: Setting TZ env var will fix
Test: Set TZ=UTC in CI
Result: REJECTED - No effect
```

### Verification Techniques

| Technique | Description | Use Case |
|-----------|-------------|----------|
| Isolation | Run component in isolation | Identify faulty component |
| Substitution | Replace suspected component | Confirm component is cause |
| Bisection | Binary search through history | Find problematic commit |
| Instrumentation | Add logging/tracing | Understand execution path |
| Reproduction | Recreate in controlled env | Confirm understanding |

---

## Combining Methods

### When to Use Each

| Situation | Recommended Method |
|-----------|-------------------|
| Clear symptom, unclear cause | 5 Whys |
| Multiple possible causes | Hypothesis-Driven |
| Intermittent issues | Hypothesis-Driven |
| Post-incident analysis | 5 Whys |
| Performance issues | Hypothesis-Driven |
| Complex bugs | Both (5 Whys → Hypothesis) |

### Combined Workflow

```
1. Start with 5 Whys to understand the problem space
   └─ Get to 2-3 potential root causes

2. Form hypotheses for each potential cause
   └─ Rank by likelihood

3. Test hypotheses systematically
   └─ Document results

4. Apply fix based on confirmed hypothesis

5. Validate fix resolves original symptom
```

---

## Integration with /solve Skill

### --5whys Option

When invoked with `--5whys`:
- Phase 3 displays detailed 5 Whys chain
- Each Why level includes evidence
- Final root cause is highlighted
- Direct handoff to Phase 5 resolution

### --hypothesis Option

When invoked with `--hypothesis`:
- Phase 4 is enhanced with structured hypothesis testing
- Multiple hypotheses are tracked
- Each hypothesis has status tracking
- Results inform fix approach in Phase 5

### Default Mode

Without options:
- Uses 5 Whys in Phase 3 (via root-cause-finder agent)
- Lightweight hypothesis verification in Phase 4
- Balanced approach for most issues
