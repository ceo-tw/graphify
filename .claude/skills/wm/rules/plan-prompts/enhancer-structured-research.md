---
title: Structured Research
type: enhancer
source: .claude/docs/claude-code-prompt/07-specialized-domains/research-gathering.md
applicable_to: strategic, architect
priority: MEDIUM
---

# Enhancer: Structured Research

> Systematic hypothesis-based information gathering and analysis

## Purpose

- Structured approach to complex investigation tasks
- Efficient information gathering through hypothesis-based approach
- Verified conclusions through confidence tracking

## Pattern

<structured_research>
Search for this information in a structured way:

1. Develop competing hypotheses as you gather data
2. Track confidence levels in your progress notes
3. Regularly self-critique your approach and plan
4. Update a hypothesis tree or research notes file
5. Break down complex research systematically

This approach allows finding and synthesizing virtually any information,
iteratively critiquing findings regardless of corpus size.
</structured_research>

## Research Workflow

### Phase 1: Scoping

<research_scoping>
Before deep research:

1. Define the research question clearly
2. Identify what's already known
3. Determine scope boundaries
4. List potential source types
5. Set success criteria
</research_scoping>

### Phase 2: Gathering

<research_gathering>
Systematic information gathering:

1. Start with broad searches
2. Follow promising leads
3. Document all sources
4. Track what's been searched
5. Note gaps in available information
</research_gathering>

### Phase 3: Analysis

<research_analysis>
Analyze gathered information:

1. Organize by theme/topic
2. Identify patterns and contradictions
3. Evaluate source quality
4. Synthesize key findings
5. Note remaining uncertainties
</research_analysis>

## When to Use

- Complex requirements analysis (Strategic Role)
- Investigation for architecture decisions (Architect Role)
- Analyzing existing codebase patterns
- Comparative analysis for technology selection

## Hypothesis-Driven Research

<hypothesis_research>
For complex research, use hypothesis-driven approach:

1. Form initial hypotheses based on question
2. Search for evidence supporting/refuting each
3. Update hypothesis tree as evidence accumulates
4. Track confidence in each hypothesis
5. Iterate until clear conclusion or uncertainty is understood

Example hypothesis tree:
- H1: Bug is in authentication module (60% confidence)
  - Evidence for: Error occurs after login
  - Evidence against: Logs show auth succeeds
- H2: Bug is in session management (35% confidence)
  - Evidence for: Session token format changed
  - Evidence against: Not reproduced in isolation

Update confidences as research progresses.
</hypothesis_research>

## Integration Example

```python
# Strategic analysis with structured research
role_prompt = Read("rules/role-strategic-phase-decomposition.md")
enhancer = Read("rules/enhancer-structured-research.md")

combined = f"""
{role_prompt}

{enhancer}

When analyzing complex requirements:
1. Form hypotheses
2. Gather evidence from codebase
3. Track confidence levels
"""

Task(subagent_type="design", prompt=combined, model="opus")  # or planner-task for TACTICAL
```

## Research State Tracking

```json
{
  "question": "What architecture pattern should we use?",
  "hypotheses": [
    {
      "id": "H1",
      "description": "Layered Architecture",
      "confidence": 0.4,
      "evidence_for": ["Existing code uses layers"],
      "evidence_against": ["Complex cross-cutting concerns"]
    },
    {
      "id": "H2",
      "description": "Hexagonal Architecture",
      "confidence": 0.6,
      "evidence_for": ["Better testability needed", "Multiple adapters"],
      "evidence_against": ["Team unfamiliar"]
    }
  ],
  "sources_checked": [
    "src/services/",
    "src/controllers/",
    "package.json"
  ],
  "next_actions": ["Check test structure", "Review similar projects"]
}
```

## Research Quality Checks

<research_quality>
Before concluding research, verify:

[ ] Research question clearly answered
[ ] Multiple sources consulted
[ ] Conflicting info addressed
[ ] Confidence levels appropriate
[ ] Remaining uncertainties documented
[ ] Sources properly cited
[ ] Findings clearly organized
</research_quality>

## Related

- [Investigate Before Answering](enhancer-investigate-before-answering.md)
- [Code Exploration](enhancer-code-exploration.md)

## Source

Extracted from: `.claude/docs/claude-code-prompt/07-specialized-domains/research-gathering.md`
