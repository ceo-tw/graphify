# domains.yaml Schema Definition

**Purpose**: Define project domains for multi-domain context management

## Expected Schema

```yaml
version: "1.0"
type: "domains"
last_updated: "YYYY-MM-DD"

items:
  - id: "DOM-XXX"                    # Unique domain ID
    name: "string"                    # Human-readable name
    directory: "path/to/domain"       # Directory path from project root
    agentsFile: "path/to/AGENTS.md"   # AGENTS.md file path
    guideFile: "path/to/guide.md"     # Optional guide file path (nullable)
    type: "frontend|backend|database|client|deploy|tray-app"  # Domain type
    techStack: ["tech1", "tech2"]     # Technology stack
    keywords: ["kw1", "kw2"]          # Search keywords
    priority: "CRITICAL|HIGH|MEDIUM|LOW"  # Domain priority
    description: "string"             # Domain description
    validation:
      type: "exists"                  # Validation type
```

## Required Fields

1. **id** (string, required): Unique identifier (DOM-XXX format)
2. **name** (string, required): Human-readable domain name
3. **directory** (string, required): Relative path from project root
4. **agentsFile** (string, required): Path to AGENTS.md file
5. **guideFile** (string, optional): Path to guide file (can be null)
6. **type** (enum, required): Domain type classification
7. **techStack** (array, required): List of technologies used
8. **keywords** (array, required): Search keywords for domain identification
9. **priority** (enum, required): CRITICAL, HIGH, MEDIUM, LOW
10. **description** (string, required): Domain description
11. **validation** (object, required): Validation configuration

## Domain Types

- **frontend**: UI/UX layer (e.g., Next.js, React)
- **backend**: API/Service layer (e.g., Node.js, Python)
- **database**: Data layer (e.g., ClickHouse, PostgreSQL)
- **client**: Client tools/scripts (e.g., Shell, CLI)
- **deploy**: Deployment/Infrastructure (e.g., Kubernetes)
- **tray-app**: Desktop application (e.g., macOS app)

## Validation Rules

1. **Directory Existence**: Directory path must exist
2. **AGENTS.md Existence**: agentsFile path must point to valid file
3. **Guide File (if specified)**: guideFile must exist if not null
4. **Unique IDs**: All domain IDs must be unique
5. **Valid Type**: Type must be one of the allowed domain types

## Expected Domains for claude-monitoring Project

Based on AGENTS.md context map:

1. **DOM-001**: frontend (dashboard/) - Next.js UI layer
2. **DOM-002**: backend (collector/) - JSONL ingestion service
3. **DOM-003**: database (docker/) - ClickHouse + OTel infrastructure
4. **DOM-004**: client (client/) - Mac bootstrap scripts
5. **DOM-005**: deploy (deploy/) - Kubernetes deployment config
6. **DOM-006**: tray-app (tray-app/) - macOS menu bar app

## Usage Example

```yaml
# Adding a new domain (e.g., shared library)
- id: "DOM-007"
  name: "shared"
  directory: "packages/shared"
  agentsFile: "packages/shared/AGENTS.md"
  guideFile: null
  type: "backend"
  techStack: ["TypeScript", "Node.js"]
  keywords: ["shared", "library", "utils"]
  priority: "MEDIUM"
  description: "Shared utilities and common code"
  validation:
    type: "exists"
```

## References

- [folders.yaml](./folders.yaml) - Directory structure registry pattern
- [skills.yaml](./skills.yaml) - Skill registry pattern
- [agents.yaml](./agents.yaml) - Agent registry pattern
