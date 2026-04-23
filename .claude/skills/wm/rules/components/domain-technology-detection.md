# Domain and Technology Detection (Shared Component)

Shared detection logic for loading domain rules and technology-specific best practices.
Used by: `dev-executor`, `bug-fixer`, `qa`

---

## Two-Step Strategy (if/else - mutually exclusive)

### Step A: Load Domain Rules from Context (PREFERRED)

Load rules from Task metadata or input context if available:

```python
# For dev-executor: from Task metadata
rules = task.metadata.get("rules", [])
domains = task.metadata.get("domains", [])

# For bug-fixer: from input context
# rules = input_context.get("rules", [])
# domains = input_context.get("domains", [])

if rules:
    for rule in rules:
        Read(file_path=rule)
    # Domain-specific AGENTS.md loading
    agents_md_map = {
        "frontend": "dashboard/AGENTS.md",
        "backend": "collector/AGENTS.md",
        "database": "docker/AGENTS.md",
        "client": "client/AGENTS.md"
    }
    for domain in domains:
        if domain in agents_md_map:
            Read(file_path=agents_md_map[domain])
    # DONE - Skip Step B
```

### Step B: Technology Detection Fallback (only when Step A has no rules)

File extension-based detection when no domain metadata:

```python
if target_file.endswith(('.ts', '.tsx')):
    tech_stack = 'typescript'
    Read(file_path=".claude/skills/best-practices/rules/ts-index.md")
    if target_file.endswith('.tsx') or 'react' in project_dependencies:
        Read(file_path=".claude/skills/best-practices/rules/react-index.md")
        # Next.js/Frontend project detection
        if file_exists(f"{project_dir}/AGENTS.md"):
            Read(file_path=".claude/skills/wm/rules/policies/guide-frontend.md")
            Read(file_path=f"{project_dir}/AGENTS.md")

elif target_file.endswith('.py'):
    tech_stack = 'python'
    Read(file_path=".claude/skills/best-practices/rules/py-index.md")

elif target_file.endswith('.go'):
    tech_stack = 'go'
    Read(file_path=".claude/skills/best-practices/rules/go-index.md")

elif target_file.endswith('.rs'):
    tech_stack = 'rust'
    Read(file_path=".claude/skills/best-practices/rules/rust-index.md")

elif target_file.endswith('.sh'):
    tech_stack = 'shell'
    Read(file_path=".claude/skills/wm/rules/policies/guide-client.md")
    Read(file_path="client/AGENTS.md")

elif target_file.endswith('.sql'):
    tech_stack = 'sql'
    Read(file_path=".claude/skills/wm/rules/policies/guide-database.md")
    Read(file_path="docker/AGENTS.md")

else:
    tech_stack = None  # Unsupported (graceful fallback)
```

---

## References

- [Best Practices Skill](../../best-practices/SKILL.md)
- [Frontend Guide](../policies/guide-frontend.md) - Next.js/React
- [Backend Guide](../policies/guide-backend.md) - TypeScript/Zod
- [Database Guide](../policies/guide-database.md) - ClickHouse/SQL
- [Client Guide](../policies/guide-client.md) - Shell/BATS
