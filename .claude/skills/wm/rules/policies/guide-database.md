---
title: Database Development Reference
type: guide
impact: HIGH
used_by: [design, planner-task, dev-executor]
domain: database
---

# Database Development Reference

> **Purpose**: Essential principles for /planner workflow in ClickHouse database projects
> **Scope**: Generic patterns for ClickHouse databases, adaptable to project-specific needs

---

## 1. Schema Naming Conventions (Required)

### 1.1 Table Naming

```sql
-- Source tables: otel_<signal>
otel_logs, otel_metrics_sum, otel_traces

-- JSONL tables: jsonl_<entity>
jsonl_session_logs, jsonl_conversations

-- Materialized View targets: <entity>_<aggregation>
metrics_1m, sessions_daily, user_stats_hourly

-- Auxiliary tables: <domain>_<purpose>
team_budgets, known_saas_patterns

-- Views: v_<entity>_<purpose>
v_active_teams, v_user_summary
```

### 1.2 Column Naming

```sql
-- snake_case required
timestamp_1m, user_email, session_count

-- Type suffix recommended
TimeUnix         -- Unix timestamp
timestamp_1m     -- Aggregated timestamp
cost_usd         -- Currency unit
duration_ms      -- Time unit
```

---

## 2. TTL Policies (Required)

### 2.1 Standard TTL Rules

```sql
-- Raw data: 14 days (short-term retention)
ENGINE = MergeTree
ORDER BY (Timestamp)
TTL toDateTime(Timestamp) + INTERVAL 14 DAY;

-- Aggregated data: 365 days (long-term retention)
TTL toDateTime(timestamp_1m) + INTERVAL 365 DAY;

-- JSONL data: 30 days
TTL toDateTime(timestamp) + INTERVAL 30 DAY;
```

### 2.2 TTL by Data Type

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Raw OTEL | 14 days | High volume, aggregated in MV |
| JSONL Sessions | 30 days | Detailed replay needs |
| Minute aggregations | 90 days | UI queries |
| Daily aggregations | 365 days | Trend analysis |

---

## 3. Idempotent DDL (Required)

### 3.1 Always Use IF NOT EXISTS / IF EXISTS

```sql
-- ✅ Correct: Idempotent statements
CREATE TABLE IF NOT EXISTS teams (
    id UUID DEFAULT generateUUIDv4(),
    name String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree
ORDER BY id;

CREATE VIEW IF NOT EXISTS v_active_teams AS
SELECT * FROM teams WHERE is_active = 1;

ALTER TABLE teams ADD COLUMN IF NOT EXISTS new_column String;

-- ❌ Prohibited: Non-idempotent statements
CREATE TABLE teams (...);  -- Fails on re-run
```

### 3.2 Migration File Structure

```sql
-- Migration: 007_add_feature.sql
-- Purpose: Add new feature table and related columns
-- Date: 2026-01-28
-- PRD: docs/PRD/feature-prd.md

USE uptrace;

-- 1. Create new table
CREATE TABLE IF NOT EXISTS new_feature (
    id UUID DEFAULT generateUUIDv4(),
    -- columns...
) ENGINE = MergeTree
ORDER BY id;

-- 2. Add columns to existing tables
ALTER TABLE existing_table
    ADD COLUMN IF NOT EXISTS feature_id UUID;

-- 3. Create indexes
-- Note: ClickHouse doesn't support CREATE INDEX IF NOT EXISTS
-- Use ALTER TABLE ADD INDEX instead

-- 4. Create MV if needed
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_new_feature
TO new_feature_aggregated
AS SELECT ... FROM new_feature ...;
```

---

## 4. MV (Materialized View) Patterns (Required)

### 4.1 Standard MV Structure

```sql
-- MV with explicit target table (recommended)
CREATE TABLE IF NOT EXISTS metrics_1m_table (
    timestamp_1m DateTime,
    user_email String,
    session_count UInt64,
    token_total UInt64
) ENGINE = SummingMergeTree
ORDER BY (timestamp_1m, user_email);

CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_1m
TO metrics_1m_table
AS SELECT
    toStartOfMinute(TimeUnix) AS timestamp_1m,
    extractAttribute('user.email') AS user_email,
    count() AS session_count,
    sum(Value) AS token_total
FROM otel_metrics_sum
WHERE MetricName = 'claude_code.token.usage'
GROUP BY timestamp_1m, user_email;
```

### 4.2 MV Modification Procedure

```sql
-- MV cannot be modified directly. Must recreate:

-- Step 1: Drop MV (keeps target table data)
DROP VIEW IF EXISTS metrics_1m;

-- Step 2: Recreate MV with new logic
CREATE MATERIALIZED VIEW metrics_1m
TO metrics_1m_table
AS SELECT
    -- new query logic
FROM otel_metrics_sum ...;

-- Step 3: Backfill if needed
INSERT INTO metrics_1m_table
SELECT ... FROM otel_metrics_sum
WHERE TimeUnix >= toDateTime('2026-01-01');
```

### 4.3 Engine Selection

| Use Case | Engine | Properties |
|----------|--------|------------|
| Sum aggregations | SummingMergeTree | Auto-sums on merge |
| Count/Latest | ReplacingMergeTree | Keeps latest row per key |
| Complex aggregations | AggregatingMergeTree | State functions |
| Raw data | MergeTree | Standard storage |

---

## 5. Rollback Strategy (Required)

### 5.1 Safe Rollback Patterns

```sql
-- Instead of DROP TABLE, rename
ALTER TABLE old_table RENAME TO old_table_deprecated;

-- Instead of DROP COLUMN, add deprecation flag
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deprecated UInt8 DEFAULT 0;

-- Create rollback script alongside migration
-- 007_add_feature.sql → 007_rollback_add_feature.sql
```

### 5.2 Irreversible Changes

```
⚠️ These changes cannot be safely rolled back:
├── DROP TABLE/VIEW (data loss)
├── ALTER TABLE DROP COLUMN (data loss)
├── TRUNCATE TABLE (data loss)
└── DELETE FROM (large scale data loss)

Mitigation:
1. Always backup before destructive operations
2. Use _deprecated suffix instead of DROP
3. Use is_deprecated flag instead of DELETE
```

---

## 6. Migration File Conventions (Required)

### 6.1 File Naming

```
{number}_{description}.sql

Examples:
- 001_fix_legacy_mv_datasource.sql
- 006_teams_schema.sql
- 007_add_user_preferences.sql
```

### 6.2 Required Header

```sql
-- Migration: 007_add_feature.sql
-- Purpose: <brief description of changes>
-- Date: YYYY-MM-DD
-- PRD: <link to related PRD document>

USE uptrace;
```

### 6.3 Migration Checklist

```
Pre-deployment:
[ ] IF NOT EXISTS/IF EXISTS used everywhere
[ ] Header with Purpose, Date, PRD reference
[ ] Local testing completed
[ ] Rollback script prepared (if needed)
[ ] Impact on dependent services verified
[ ] MV backfill plan documented (if applicable)

Post-deployment:
[ ] Verify table/view creation
[ ] Verify data population (if applicable)
[ ] Monitor query performance
```

---

## 7. Query Patterns (Recommended)

### 7.1 Time-Based Queries

```sql
-- Use toStartOf* functions for aggregation
SELECT
    toStartOfHour(timestamp) AS hour,
    count() AS count
FROM otel_logs
WHERE timestamp >= now() - INTERVAL 24 HOUR
GROUP BY hour
ORDER BY hour;

-- Use DateTime comparison, not string
WHERE timestamp >= '2026-01-01'  -- ❌ String
WHERE timestamp >= toDateTime('2026-01-01')  -- ✅ DateTime
```

### 7.2 Attribute Extraction

```sql
-- Extract from OTEL ResourceAttributes/LogAttributes
SELECT
    ResourceAttributes['user.email'] AS user_email,
    LogAttributes['event.name'] AS event_name
FROM otel_logs;

-- Alternative: JSONExtractString
SELECT
    JSONExtractString(ResourceAttributes, 'user.email') AS user_email
FROM otel_logs;
```

---

## 8. PHASE Decomposition Guide (Database-Specific)

### 8.1 Database Feature PHASE Order

```
PHASE 1: Schema Design
  - Table structure design
  - Column types and defaults
  - Index strategy
  - TTL policy

PHASE 2: Table Creation
  - CREATE TABLE statements
  - Initial indexes
  - Engine selection

PHASE 3: MV Creation
  - Target table creation
  - MV query logic
  - Backfill strategy

PHASE 4: Integration
  - Application integration points
  - Query optimization
  - Monitoring setup
```

### 8.2 Layer Mapping

| Clean Architecture | Database Equivalent |
|--------------------|---------------------|
| Domain | Table schemas, business rules |
| Application | Views, stored procedures |
| Adapters | MV query logic |
| Infrastructure | Engine config, TTL, indexes |

---

## 9. Quality Commands

```bash
# SQL lint (ClickHouse dialect)
sqlfluff lint {database_dir}/clickhouse/*.sql --dialect clickhouse

# YAML lint (for config files)
yamllint {database_dir}/**/*.yml

# Apply migration (local)
docker exec -it clickhouse-server clickhouse-client \
  --query "source /tmp/007_migration.sql"

# Verify schema
docker exec clickhouse-server clickhouse-client \
  --query "DESCRIBE TABLE uptrace.new_table"
```

---

## 10. Project-Specific Guidelines Reference

Check additional guidelines in your project's AGENTS.md file:

- **Infrastructure projects**: `{infra_dir}/AGENTS.md` or `{project_dir}/AGENTS.md` - Database config, deployment patterns
- **Project root**: `{project_dir}/AGENTS.md` - Overall project guidelines
