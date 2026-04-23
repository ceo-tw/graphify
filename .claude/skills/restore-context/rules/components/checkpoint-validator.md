# Checkpoint Validator Component

## Purpose

Validate checkpoint schema based on version.

## Schema Definitions

### v4.0 Schema
```json
{
  "version": "4.0",
  "max_checkpoints": 5,
  "checkpoints": [
    {
      "slot": 0,
      "timestamp": "ISO-8601",
      "session_id": "string",
      "transcript_path": "string",
      "current_work": {
        "plan_path": "string",
        "status": "string",
        "last_agent": "string|null",
        "last_agent_id": "string|null"
      },
      "completed_phases": [],
      "plans_tree": "string",
      "summary": "string"
    }
  ]
}
```

### v3.0 Schema
```json
{
  "version": "3.0",
  "timestamp": "ISO-8601",
  "session_id": "string",
  "transcript_path": "string",
  "current_work": {...},
  "completed_phases": [],
  "plans_tree": "string"
}
```

### v1.0 Schema (Legacy)
```json
{
  "version": "1.0",
  "timestamp": "ISO-8601",
  "plan_name": "string",
  "current_phase": 1,
  "phase_status": "string"
}
```

## Implementation

```python
def validate_checkpoint_schema(data, version):
    """Validate checkpoint data against schema."""

    if version == "4.0":
        # v4: Must have checkpoints array with at least one entry
        checkpoints = data.get("checkpoints", [])
        if not isinstance(checkpoints, list) or len(checkpoints) == 0:
            return {"valid": False, "error": "v4 requires non-empty checkpoints array"}
        return {"valid": True, "checkpoints": checkpoints, "count": len(checkpoints)}

    elif version == "3.0":
        # v3: Must have timestamp and session_id
        required = ["timestamp", "session_id"]
        missing = [f for f in required if f not in data]
        if missing:
            return {"valid": False, "error": f"v3 missing fields: {missing}"}
        return {"valid": True, "checkpoints": [data], "count": 1}

    else:
        # v1.x: Must have plan_name and current_phase
        required = ["plan_name", "current_phase"]
        missing = [f for f in required if f not in data]
        if missing:
            return {"valid": False, "error": f"v1 missing fields: {missing}"}
        return {"valid": True, "checkpoints": [data], "count": 1}
```

## Validation Rules

1. **v4.0**: `checkpoints` must be a non-empty array
2. **v3.0**: `timestamp` and `session_id` must exist
3. **v1.x**: `plan_name` and `current_phase` must exist

## Error Handling

Return structured error with:
- `valid`: boolean
- `error`: string (if invalid)
- `checkpoints`: array (if valid)
- `count`: number (if valid)
