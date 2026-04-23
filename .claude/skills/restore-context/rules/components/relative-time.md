# Relative Time Component

## Purpose

Convert ISO-8601 timestamps to human-readable Korean relative time strings.

## Output Format

| Time Difference | Output |
|-----------------|--------|
| < 60 seconds | "방금 전" |
| < 60 minutes | "N분 전" |
| < 24 hours | "N시간 전" |
| >= 24 hours | "N일 전" |
| Invalid/Unknown | "알 수 없음" |

## Implementation

```python
from datetime import datetime, timezone

def calculate_relative_time(timestamp_str):
    """Convert ISO timestamp to relative time string in Korean."""
    if not timestamp_str or timestamp_str == "unknown":
        return "알 수 없음"

    try:
        # Parse ISO-8601 timestamp
        ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - ts

        total_seconds = delta.total_seconds()

        if total_seconds < 60:
            return "방금 전"
        elif total_seconds < 3600:
            minutes = int(total_seconds / 60)
            return f"{minutes}분 전"
        elif total_seconds < 86400:
            hours = int(total_seconds / 3600)
            return f"{hours}시간 전"
        else:
            days = int(total_seconds / 86400)
            return f"{days}일 전"
    except Exception:
        return "알 수 없음"
```

## Usage

```python
# Example usage
relative_time = calculate_relative_time("2026-01-25T12:00:00Z")
# Output: "3시간 전" (depending on current time)
```

## Cross-Platform Notes

This component is also implemented in `hook-utils.sh` for shell scripts:

```bash
# Uses parse_iso_timestamp() which handles both:
# - macOS: date -j -f "%Y-%m-%dT%H:%M:%SZ" "${timestamp}" +%s
# - Linux: date -d "${timestamp}" +%s
```
