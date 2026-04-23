# Worktree Path Rules (MANDATORY)

When `worktree_path` is provided in the prompt, ALL file operations must use absolute paths.

## File Operations

```python
# Reading files
Read(file_path=f"{worktree_path}/src/domain/entities/User.ts")

# Writing files
Write(file_path=f"{worktree_path}/tests/unit/User.test.ts", content=...)

# Editing files
Edit(file_path=f"{worktree_path}/src/application/usecases/CreateUser.ts", ...)

# Pattern search
Glob(pattern="**/*.test.ts", path=f"{worktree_path}/src/")
Grep(pattern="export class.*Service", type="ts", path=f"{worktree_path}/src/")
```

## Bash Commands

All bash commands MUST use `cd {worktree_path} &&` prefix:

```python
# Test execution
Bash(command=f"cd {worktree_path} && bun run test -- {test_file}")

# Build
Bash(command=f"cd {worktree_path} && bun run build")

# Lint
Bash(command=f"cd {worktree_path} && bun run lint")

# Type check
Bash(command=f"cd {worktree_path} && bun run type-check")

# Git operations
Bash(command=f"cd {worktree_path} && git status")
```

## LSP Operations

```python
LSP(
    operation="goToDefinition",
    filePath=f"{worktree_path}/src/domain/entities/User.ts",
    line=10,
    character=14
)
```

## Script Invocation Safety (CRITICAL)

When invoking `.claude/scripts/` from worktree context:

### Rule 1: Always Use Worktree's Script Copy

```python
# CORRECT: Use worktree's copy of script
Bash(command=f"cd {worktree_path} && ./.claude/scripts/skill-lifecycle.sh --repo-root {worktree_path} deactivate test-skill")

# WRONG: Never use absolute path to main repo script
Bash(command="/path/to/main/.claude/scripts/skill-lifecycle.sh deactivate test-skill")  # DANGER!
```

### Rule 2: Always Provide --repo-root Parameter

```python
# CORRECT: Explicit repo root
Bash(command=f"cd {worktree_path} && ./.claude/scripts/skill-lifecycle.sh --repo-root {worktree_path} list")

# DANGEROUS: No explicit path (may operate on main repo)
Bash(command=f"cd {worktree_path} && ./.claude/scripts/skill-lifecycle.sh list")  # AVOID!
```

### Rule 3: Verify Target Before Destructive Operations

```python
# 1. Log the target directory
print(f"Target repository: {worktree_path}")

# 2. Verify worktree_path is set and valid
assert worktree_path, "worktree_path must be set"

# 3. Call script with explicit path
Bash(command=f"cd {worktree_path} && ./.claude/scripts/skill-lifecycle.sh --repo-root {worktree_path} deactivate skill-name")
```

## CRITICAL: NEVER Use Relative Paths

When `worktree_path` exists:
- `Read(file_path="src/file.ts")` - WRONG
- `Read(file_path=f"{worktree_path}/src/file.ts")` - CORRECT

Each Bash call has isolated working directory - `cd` is NOT persistent between calls.
