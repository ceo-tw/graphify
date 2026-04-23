# Checkpoint Reader Component

## Purpose

Read and parse the checkpoint JSON file.

## File Location

```
.claude/workflow-checkpoint.json
```

## Implementation

```python
import json
import os

def read_checkpoint():
    """Read checkpoint file and return parsed data."""
    project_root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    checkpoint_path = f"{project_root}/.claude/workflow-checkpoint.json"

    # Check file existence
    if not os.path.exists(checkpoint_path):
        return {"error": "no_checkpoint", "path": checkpoint_path}

    # Read file content
    try:
        with open(checkpoint_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {"error": "file_read_failed", "details": str(e)}

    # Parse JSON
    try:
        data = json.loads(content)
        version = data.get("version", "1.0")
        return {"success": True, "data": data, "version": version, "path": checkpoint_path}
    except json.JSONDecodeError as e:
        return {"error": "corrupted_json", "details": str(e)}
```

## Usage

```python
result = read_checkpoint()
if "error" in result:
    # Handle error based on result["error"]
    pass
else:
    checkpoint_data = result["data"]
    version = result["version"]
```

## Error Codes

| Code | Description |
|------|-------------|
| `no_checkpoint` | File does not exist |
| `file_read_failed` | Cannot read file (permissions, etc.) |
| `corrupted_json` | Invalid JSON syntax |
