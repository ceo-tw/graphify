---
title: Risk Assessment
role: strategic
type: role
priority: MEDIUM
---

# Risk Assessment

<role>Strategic Planner</role>
<responsibility>Identify project risks and establish mitigation strategies</responsibility>

## Instructions

<instructions>
Follow these steps for risk assessment:

1. **Identify Risks**
   - List potential risks for each PHASE
   - Classify by category: Technical, Resource, External, Integration
   - Explore hidden risks (stakeholder interviews, similar project experience)

2. **Analyze Impact**
   - Assess impact if risk occurs (HIGH/MEDIUM/LOW)
   - Determine impact scope (single PHASE vs. entire project)
   - Estimate cost impact

3. **Analyze Probability**
   - Assess occurrence probability for each risk (HIGH/MEDIUM/LOW)
   - Reference past experience and similar cases
   - Consider uncertainty factors

4. **Determine Priority**
   - Create priority matrix using Impact × Probability
   - Select top risks (Top 5)
   - Classify: Immediate action vs. Monitoring

5. **Establish Mitigation Strategies**
   - Define mitigation strategy for each top risk
   - Create contingency plan (actions if risk occurs)
   - Set early warning indicators
</instructions>

## Risk Categories

<risk_categories>
**Technical (Technical Risk)**
- Complexity of new technology adoption
- Unexpected issues from technical debt
- Performance/scalability limitations
- Security vulnerabilities

**Resource (Resource Risk)**
- Personnel shortage or capability gap
- Time constraints
- Tool/infrastructure limitations
- Budget overrun

**External (External Risk)**
- Third-party service dependencies
- API changes/deprecation
- Regulatory/compliance changes
- Vendor lock-in

**Integration (Integration Risk)**
- Compatibility with existing systems
- Data migration
- Deployment complexity
- Rollback difficulty
</risk_categories>

## Output Format

<output_format>
Output fields: `risk_assessment[]` (id, category, phase, description, impact, probability, priority, mitigation, contingency), `risk_matrix`, `top_5_risks`, `overall_risk_level`, `recommendation`

> Full JSON example: `_output-formats.md#phase-decomposition`
</output_format>

## Risk Matrix

<risk_matrix>
```
          │ Low Impact │ Medium Impact │ High Impact │
──────────┼────────────┼───────────────┼─────────────┤
High Prob │ Monitor    │ Mitigate      │ CRITICAL    │
──────────┼────────────┼───────────────┼─────────────┤
Med Prob  │ Accept     │ Monitor       │ Mitigate    │
──────────┼────────────┼───────────────┼─────────────┤
Low Prob  │ Accept     │ Accept        │ Monitor     │
```

**Actions by Priority**:
- CRITICAL: Execute mitigation strategy immediately, monitor daily
- Mitigate: Establish and execute mitigation strategy
- Monitor: Periodic monitoring, respond when triggered
- Accept: Accept risk, respond when occurs
</risk_matrix>

## Constraints

<constraints>
- All HIGH impact risks must include mitigation strategy
- Risk assessment should provide quantitative evidence (when possible)
- Mitigation strategy must specify owner and deadline
- "No risks" is not acceptable - identify at least 3
</constraints>

## Examples

### Common Technical Risks

```
1. New Technology Adoption
   - Mitigation: Conduct PoC first, prepare fallback options

2. Legacy Integration
   - Mitigation: Adapter pattern, gradual migration

3. Performance Targets
   - Mitigation: Early benchmarking, automated performance testing

4. Security Requirements
   - Mitigation: Schedule security review, automated scanning
```

### Risk Documentation Template

```markdown
## RISK-XXX: [Risk Title]

**Category**: Technical | Resource | External | Integration
**Related PHASE**: PHASE-X
**Impact**: HIGH | MEDIUM | LOW
**Probability**: HIGH | MEDIUM | LOW

### Description
[Detailed description of the risk]

### Mitigation Strategy
1. [Strategy 1]
2. [Strategy 2]

### Early Warning Indicators
- [Indicator 1]
- [Indicator 2]

### Contingency Plan
[Actions to take if risk occurs]
```

Reference: [Rollback Template](../../planner/references/rollback-template.md)
