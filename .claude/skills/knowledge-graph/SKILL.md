---
name: knowledge-graph
type: workflow
description: "Graphify CLI wrapper — 18개 물리 도메인 그래프(legacy v0.4.x, undirected) + _global v0.5.2 directed overlay. URL 중심 질의(resolve/callers/callees/blast)는 _global, 도메인 요약·god-node는 18 도메인 그래프. 재구현 금지 — Graphify·scripts/graphify/*.ts의 얇은 래퍼."
argument-hint: "[build|update|domain|matrix|query|path|explain|validate|hotspots|coverage|diff|mcp-serve|resolve|callers|callees|blast|init-ignore] [args...]"
allowed-tools: [Bash, Read, Glob, Grep]
user-invocable: true
---

# /knowledge-graph

openclaw-cloud 3차원 카테고라이즈(18 물리 그래프 · 14 도메인 · 13 Ontology) + `_global` URL/API overlay 기반 지식 그래프 관리 도구.

## 두 세계 (v0.4.21 legacy + v0.5.2 global)

| 세계 | 대상 | directed | 커맨드 | 사용 |
|---|---|---|---|---|
| **Domain graphs (legacy)** | 18 물리 그래프 (audit-logs, billing, ...) | `false` (undirected) | `build`, `update`, `domain`, `matrix`, `query`, `path`, `explain`, `validate`, `hotspots`, `coverage`, `diff`, `mcp-serve` | 도메인별 god-node, community 탐색, manifest ↔ 코드 매트릭스 검증 |
| **_global overlay (v0.5.2)** | 전 프로젝트 URL·API·HTTP 체인 | `true` | `resolve`, `callers`, `callees`, `blast`, `init-ignore` | URL 1줄로 FE→BE 체인 추적 |

## 원칙

- 모든 로직은 Graphify CLI 또는 `scripts/graphify/*.ts`의 **얇은 래퍼**. **재구현 금지**.
- **EXTRACTED edge만 하드 검증에 사용**. INFERRED/AMBIGUOUS는 info 표시.
- Pass 3(semantic) 기본 OFF — docs/ADR에만 opt-in.
- tasks-service처럼 EXTRACTED < 85%인 그래프는 warn 대상.
- `callers`/`callees`/`blast`는 **정확한 id 또는 정확한 label** 일치 필수 (v0.5.2 계약). 퍼지 매치 아님.
- API 노드 label 형식: `METHOD path` (예: `POST /agents/:id/restart`). `API:` 접두사 없음.
- URL 노드 label 형식: `URL <pattern>` (예: `URL /portal/agents/:id`).

---

## Commands

### /knowledge-graph build [graph-name]

단일 또는 모든 18 그래프를 AST 기반으로 빌드.

```bash
# 전체 빌드 (audit-logs는 이미 파일럿 완료됐으면 skip)
node --experimental-strip-types --no-warnings $CLAUDE_PROJECT_DIR/scripts/graphify/build-all-graphs.ts

# 단일
node --experimental-strip-types --no-warnings $CLAUDE_PROJECT_DIR/scripts/graphify/build-all-graphs.ts --only billing

# 재빌드 (audit-logs 포함)
node --experimental-strip-types --no-warnings $CLAUDE_PROJECT_DIR/scripts/graphify/build-all-graphs.ts --rebuild
```

### /knowledge-graph update [graph-name]

기존 그래프에 `graphify update` 증분 재추출. LLM 비용 0 (코드 파일만).

```bash
cd $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify update corpus
```

### /knowledge-graph domain <Y>

특정 도메인의 그래프 정보 통합 뷰 (해당 도메인의 물리 그래프 리스트 + god-node 통합).

```bash
# 예: /knowledge-graph domain billing
# → billing 그래프 (single X) 결과 요약
cat $CLAUDE_PROJECT_DIR/.claude/architecture/graph/billing/graphify-out/GRAPH_REPORT.md
```

### /knowledge-graph matrix <Y> <Z>

특정 (도메인, 노드 카테고리) 좌표의 manifest 섹션 + 실제 코드 매핑.

```bash
# 예: /knowledge-graph matrix billing Provider
# → providers.yml의 billing 도메인 항목 + 실제 코드 참조
grep -A 20 "domain: billing" $CLAUDE_PROJECT_DIR/.claude/manifests/providers.yml
```

### /knowledge-graph query "질문"

Graphify 공식 BFS 탐색.

```bash
# 특정 그래프에 대해 쿼리
cd $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify query "tenant isolation in billing"
```

### /knowledge-graph path "NodeA" "NodeB"

두 노드 간 최단 경로.

```bash
cd $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify path "recordAudit" "useAuditLogs"
```

### /knowledge-graph explain "NodeName"

단일 노드의 이웃 관계 설명.

```bash
cd $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify explain "TossProvider"
```

### /knowledge-graph validate [area]

3축 매트릭스 교차 검증 (PHASE 6 스크립트).

```bash
# 전체
node --experimental-strip-types --no-warnings $CLAUDE_PROJECT_DIR/scripts/graphify/graphify-matrix-diff.ts

# 특정 영역 (api|rbac|env|contract|provider)
node --experimental-strip-types --no-warnings $CLAUDE_PROJECT_DIR/scripts/graphify/graphify-matrix-diff.ts --check api

# violation 시 exit 1 (CI용)
node --experimental-strip-types --no-warnings $CLAUDE_PROJECT_DIR/scripts/graphify/graphify-matrix-diff.ts --fail-on error
```

### /knowledge-graph hotspots [graph-name]

in-degree 상위 god-node 목록.

```bash
# GRAPH_REPORT.md의 God Nodes 섹션 추출
grep -A 20 "## God Nodes" $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]/graphify-out/GRAPH_REPORT.md
```

### /knowledge-graph coverage

테스트 엣지 없는 노드 (테스트 커버리지 갭).

```bash
# 그래프 노드 중 tests 파일과 연결 없는 노드
# 구현은 graph.json 파싱. scripts/graphify/coverage-check.ts (차후 추가)
```

### /knowledge-graph diff

마지막 빌드 이후 그래프 변경점 (post-commit hook 연동용).

```bash
# graphify update 실행 시 내부 diff 출력 활용
cd $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify update corpus 2>&1 | grep -A 5 "diff"
```

### /knowledge-graph mcp-serve <graph-name>

MCP stdio server 백그라운드 기동 (knowledge-graph-navigator 에이전트 backbone).

```bash
# 단일 그래프에 대한 MCP 서버
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/python -m graphify.serve \
  $CLAUDE_PROJECT_DIR/.claude/architecture/graph/[graph-name]/graphify-out/graph.json
```

노출 tool: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`.

---

## URL-centric queries (v0.5.2 `_global` 전용)

모든 커맨드는 `--graph $CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json` 사용 필수. 18 도메인 그래프는 undirected라 역방향 질의 지원 안 함.

### /knowledge-graph resolve <url>

구체 URL을 받아 매칭되는 `kind="url"` 또는 `kind="api"` overlay 노드 + 1-hop 이웃 반환. (label 형식은 `URL <pattern>` / `METHOD path` — `API:` 접두사 없음)

```bash
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify resolve /portal/agents/172 --json \
  --graph $CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json

# 메서드 필터
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify resolve /agents/:id/start --method POST --json \
  --graph $CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json
```

### /knowledge-graph callers <node>

`<node>`로 전이적으로 도달하는 upstream 노드 목록 (DiGraph 필수).

**주의**:
- 대상은 **정확한 id 또는 정확한 label** (퍼지 매치 아님). label 모르면 jq로 먼저 조회.
- **named function이 namespace import로 호출하는 경우**: v0.5.2 Fix B로 정상 검출 (confidence 0.9/0.8).
- **Hono anonymous inline handler 내부 호출은 미검출** (v0.5.2 잔존, README §12.3c). `auditLogs.get('/', async (c) => { ... auditLogService.listAuditLogs(...) })` 같은 패턴은 caller anchor 부재로 `callers`가 0건으로 나올 수 있음. 0건이면 `grep -rn "<namespace>.<func>" src/.../routes/` 로 수동 보강.

```bash
# 1. id/label 확인
jq '.nodes[] | select(.label | test("listAuditLogs"; "i")) | {id, label, kind, source_file}' \
  $CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json

# 2. 정확한 id로 질의
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify callers audit_log_service_listauditlogs \
  --edges calls,calls_http --max-hops 3 --json \
  --graph $CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json
```

### /knowledge-graph callees <node>

`<node>`로부터 도달 가능한 downstream 노드 목록. 플래그는 callers와 동일.

### /knowledge-graph blast <node>

hop 제한 없는 downstream 전이 폐쇄. 파일별 그룹화된 결과 반환.

```bash
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify blast <node-id> --edges calls --json \
  --graph $CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json
```

### /knowledge-graph init-ignore

프로젝트 루트에 `.graphifyignore` 템플릿 작성/append. 기존 파일이 있으면 줄 단위 equality로 누락 패턴만 추가.

```bash
cd $CLAUDE_PROJECT_DIR && $CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify init-ignore .
```

---

## 시나리오 — URL 1줄로 FE→BE 체인 추적

"팀원이 `/portal/agents/172` 에서 '재시작' 버튼 500 오류 보고" 같은 질문에:

```bash
GRAPH=$CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json

# Step 1: URL → FE 페이지
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify resolve /portal/agents/172 --json --graph $GRAPH

# Step 2: 페이지가 호출하는 API/다운스트림 (calls + calls_http 엣지)
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify callees url_portal_agents_id \
  --edges calls,calls_http --max-hops 5 --json --graph $GRAPH

# Step 3: API → BE 핸들러 (handled_by)
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify callees api_post_agents_id_restart \
  --edges handled_by --max-hops 1 --json --graph $GRAPH

# Step 4: 핸들러 변경 시 영향 범위
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify blast <handler-id> \
  --edges calls --json --graph $GRAPH
```

### 역방향 — "이 함수를 누가 부르나"

```bash
$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify callers <func-id> \
  --edges calls,calls_http --max-hops 3 --json --graph $GRAPH
```

---

## 통합 포인트 (wm / agents)

| 워크플로우 | 호출 시점 | 사용 커맨드 |
|---|---|---|
| wm plan 단계 | design 에이전트가 영향 범위 파악 | `/knowledge-graph domain` |
| wm review 단계 | security-reviewer가 RBAC 위반 확인 | `/knowledge-graph validate rbac` |
| knowledge-graph-navigator 에이전트 | blast radius 분석 | `/knowledge-graph mcp-serve` |
| dev-executor | 변경 후 증분 업데이트 | `/knowledge-graph update` |
| PHASE 9 파일럿 | 주간 회고 | `/knowledge-graph validate` |

---

## 상태 / Precondition

- Python 3.12 venv: `.claude/graphify/.venv/` (editable install, graphify **v0.5.2** from `/Users/tw.kim/Documents/AGA/test/graphify`)
- graphify CLI: `.claude/graphify/.venv/bin/graphify`
- domain-matrix.yml + graph-splits.yml: `.claude/manifests/`
- 18 도메인 그래프 출력 (legacy v0.4.x, undirected): `.claude/architecture/graph/{name}/graphify-out/`
- `_global` overlay (v0.5.2, directed): `.claude/architecture/graph/_global/graphify-out/`
- `_global` 라벨 시드: `.claude/architecture/graph/_global/labels.json` (운영자 큐레이션)
- HTTP 래퍼 override: **openclaw에서는 불필요** (v0.5.2 자동 감지로 충분; 2026-04-19 Case A 확정 후 `src/.graphify/` 삭제됨). 타 프로젝트에서 필요 시 `<project-root>/.graphify/http-wrappers.json` 에 등록. README §8.3 참조.
- build-summary.json: 마지막 빌드 결과 요약

- `.claude/architecture/graph/build-summary.json`이 없으면 → 먼저 `/knowledge-graph build` 실행
- `_global/graphify-out/graph.json`이 없거나 `directed != true`이면 → 아래 재빌드 수행:
  ```bash
  cd $CLAUDE_PROJECT_DIR && \
    $CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify build ./src --directed \
      --out-dir .claude/architecture/graph/_global/graphify-out
  ```

---

## Out of scope

- Pass 3 (semantic extraction) 자동 실행 — docs/ADR에만 수동 opt-in
- PreToolUse hook 설치 — PHASE 9 A/B 테스트에서만 2주차 billing 한정 opt-in
- `graphify claude install` 전역 자동 실행 — 금지 (pretooluse-ab-design.md 참조)
- 외부 URL ingest (`graphify add <url>`) — 현재 계획 외

---

## References

- 계획(완료): `.claude/plans/complete/luminous-weaving-osprey.md` v4 (초기 도입) · `.claude/plans/kind-skipping-sutton.md` (v0.5.2 통합)
- 원칙: `.claude/docs/graphify/categorization-principles.md` v1
- 파일럿: `.claude/docs/graphify/phase-4-pilot-report.md`
- 운영 표준 문서: `.claude/graphify/README.md` — 디렉토리 구조, 재생성 커맨드, 알려진 제약, 운영 체크리스트
- Manifest: `.claude/manifests/{domain-matrix.yml, graph-splits.yml, glossary.yml, api-catalog.yml, rbac-matrix.yml, env-catalog.yml, contracts/billing.yml, nats-topics.yml, providers.yml, jobs.yml, adrs/, runbooks/}`
- 스크립트: `scripts/graphify/{resolve-domain-matrix.ts, build-all-graphs.ts, graphify-matrix-diff.ts}`
- Graphify: `/Users/tw.kim/Documents/AGA/test/graphify` **v0.5.2** (editable install) · fork `ceo-tw/graphify` · `GETTING_STARTED.md`
- v0.5.2 변경: v0.5.1 §12.1 JSONC 파서 버그 + §12.3b namespace import 2건 **해결** (README §A Resolution Log). openclaw `calls_http` 11→241 복구 확인. 잔존 제약: §12.2 Hono 팩토리 mount prefix 미결합, §12.3c Hono anonymous inline handler 내부 호출 caller 미검출.
