---
name: codebase-explorer
type: capability
description: "LSP 기반 코드베이스 탐색. 심볼 정의, 참조, 호출 관계 분석을 수행합니다. 사용 시점: (1) 특정 함수/클래스의 사용처를 추적할 때, (2) 코드 의존성 관계를 파악할 때, (3) 대규모 리팩토링 전 영향 범위를 분석할 때. /codebase-explorer 커맨드로 호출."
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, LSP
---

# Codebase Explorer

Navigate and understand codebases using LSP (Language Server Protocol) powered tools for precise symbol resolution, reference finding, and dependency analysis.

## LSP Operations

### Go to Definition

Find where a symbol is defined:
```
LSP goToDefinition → Returns file:line of definition
```

### Find References

Find all usages of a symbol:
```
LSP findReferences → Returns list of file:line locations
```

### Call Hierarchy

Trace incoming and outgoing calls:
```
LSP incomingCalls → What functions call this
LSP outgoingCalls → What this function calls
```

### Symbol Search

Search for symbols across the codebase:
```
LSP documentSymbol → List all symbols in a file
LSP workspaceSymbol → Search symbols across codebase
```

## When to Use

Use this skill when you need to:

```
  Scenario            Primary Tool                   When to Use
  ──────────────────  ─────────────────────────────  ───────────────────────────────────────
  Find definition     LSP goToDefinition             Navigate to where symbol is defined
  Find all usages     LSP findReferences             See everywhere symbol is used
  Call hierarchy      LSP incomingCalls/outgoingCalls Trace function call relationships
  Symbol search       find_symbol                    Find symbols by name pattern
  File structure      get_symbols_overview           Quick overview of file contents
  Type information    LSP hover                      Get type info and docs
  ──────────────────  ─────────────────────────────  ───────────────────────────────────────
```

### Tool Selection Guide

```
  Task             Best Tool               When to Use                Alternative
  ───────────────  ──────────────────────  ─────────────────────────  ────────────────────────
  Go to definition LSP goToDefinition      TypeScript/JavaScript      find_symbol
  Find references  LSP findReferences      Precise locations needed   find_referencing_symbols
  Symbol overview  get_symbols_overview    Quick structure scan       LSP documentSymbol
  Pattern search   find_symbol             Know partial name          Grep
  File discovery   Glob                    Know naming pattern        Serena list_dir
  Text search      Grep                    Search string literals     search_for_pattern
  ───────────────  ──────────────────────  ─────────────────────────  ────────────────────────
```

### Tool Preference Order

1. **LSP** - Most precise, type-aware (TypeScript, JavaScript)
2. **Serena** - Fast, pattern-based, works across languages
3. **Grep/Glob** - Fallback when above unavailable

### When NOT to Use

- Already know exact file path → `Read` directly
- Searching for text content → `Grep`
- Creating new files → `Write`

## Tools & Integration

### LSP (Primary)
- `goToDefinition` - Navigate to symbol definition
- `findReferences` - Find all usages
- `incomingCalls` / `outgoingCalls` - Call hierarchy
- `documentSymbol` - File structure
- `workspaceSymbol` - Codebase-wide search
- `hover` - Get type info and documentation

### Serena Plugin
- `find_symbol` - Locate symbols by name pattern
- `find_referencing_symbols` - Find references with context
- `get_symbols_overview` - File/module structure overview

### Grep/Glob (Fallback)
- Pattern-based search when LSP unavailable
- Find files by naming convention
- Search text patterns across codebase

## Analysis Patterns

### Dependency Mapping

```
1. Use get_symbols_overview on entry files
2. Identify import statements with Grep
3. Map internal vs external dependencies
4. Visualize dependency graph
```

### Architecture Overview

```
1. List modules/packages with Glob
2. Use get_symbols_overview on key files
3. Identify layer structure
4. Map component relationships
```

### Impact Analysis

```
1. Use findReferences on target symbol
2. Trace call hierarchy with incomingCalls
3. Identify all affected components
4. Report impact scope
```

## Workflows

### Finding Symbol Usage

1. Use LSP `findReferences` on target symbol
2. List all files and line locations
3. Use Read to show context around each usage
4. Summarize usage patterns

### Understanding Architecture

1. Use `get_symbols_overview` on key entry files
2. Map module dependencies via imports
3. Identify architectural patterns (layers, modules)
4. Present component diagram or summary

### Tracing Data Flow

1. Find data-related symbols with `find_symbol`
2. Trace references through `find_referencing_symbols`
3. Follow call hierarchy with LSP
4. Map data transformation points
5. Document complete flow path

### Analyzing Function Impact

1. Start with target function
2. Use `incomingCalls` to find callers
3. Recursively trace up the call chain
4. Use `outgoingCalls` to find dependencies
5. Report full impact scope with file:line references

---

## Essential Files Output (Adopted from feature-dev)

> **Always include an "Essential Files" section** in exploration results to provide actionable file references for follow-up tasks.

### Output Format

Every exploration result SHOULD include:

```json
{
  "analysis_summary": "...",
  "essential_files": [
    {
      "path": "src/domain/entities/User.ts:45",
      "relevance": "Core entity definition",
      "priority": 1
    },
    {
      "path": "src/application/usecases/CreateUser.ts:12",
      "relevance": "Main use case implementation",
      "priority": 2
    },
    {
      "path": "src/adapters/controllers/UserController.ts:30",
      "relevance": "API endpoint handler",
      "priority": 3
    }
  ],
  "file_count": {
    "essential": 5,
    "related": 12,
    "total_analyzed": 45
  }
}
```

### Selection Criteria

Include files as "essential" when they:

```
┌────────────────────────────────────────────────────────────────────┐
│  Criteria                        Include in Essential Files?       │
├────────────────────────────────────────────────────────────────────┤
│  Contains core business logic    ✅ Yes (priority 1)               │
│  Defines key interfaces/types    ✅ Yes (priority 2)               │
│  Entry point for feature         ✅ Yes (priority 1-2)             │
│  Configuration affecting feature ✅ Yes (priority 3)               │
│  Test file for core component    ✅ Yes (priority 3)               │
│  Utility/helper (general)        ❌ No (unless specifically used)  │
│  Type definitions only           ⚠️ Maybe (if defines key types)   │
│  External library code           ❌ No                             │
└────────────────────────────────────────────────────────────────────┘
```

### Count Guidelines

- **Essential files**: 5-10 files (most important)
- **Related files**: Up to 20 files (contextually relevant)
- **Total analyzed**: Report total for transparency

### Markdown Format Alternative

For text-based reports:

```markdown
## Essential Files (5)

1. **src/domain/entities/User.ts:45** - Core entity definition
2. **src/application/usecases/CreateUser.ts:12** - Main use case
3. **src/adapters/controllers/UserController.ts:30** - API endpoint
4. **src/domain/ports/UserRepository.ts:8** - Repository interface
5. **src/infrastructure/db/UserRepositoryImpl.ts:15** - DB implementation

## Related Files (8)
- src/application/dto/CreateUserDTO.ts
- src/domain/value-objects/Email.ts
- ...
```

### Integration with Explore Subagent

When using `Task(subagent_type="Explore")`, request essential files:

```python
Task(
    subagent_type="Explore",
    prompt="""
    Thoroughness: medium

    Analyze the authentication system.

    **IMPORTANT**: Include an "Essential Files" section with 5-10 most
    important files for understanding/modifying this feature.
    Format: path:line - brief description
    """,
    model="haiku"
)
```
