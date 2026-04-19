# graphify v0.5.0 시작하기 (fork: ceo-tw)

이 문서는 [ceo-tw/graphify](https://github.com/ceo-tw/graphify) v0.5.0 fork를 **임의의 프로젝트**에 설치해 즉시 사용할 수 있도록 돕는 실용 가이드입니다. 기존 업스트림의 `/graphify` skill 사용법은 [업스트림 README](https://github.com/safishamsi/graphify)를 참조하세요. 이 문서는 fork에서 새로 추가된 **URL 중심 워크플로우 지원** 기능에 집중합니다.

---

## 목차

- [0. 이 fork가 해결하는 문제](#0-이-fork가-해결하는-문제)
- [1. 30초 요약 — 뭐가 다른가](#1-30초-요약--뭐가-다른가)
- [2. 이 도구가 내 프로젝트에 맞는가?](#2-이-도구가-내-프로젝트에-맞는가)
- [3. 설치](#3-설치)
- [4. 첫 빌드 — 5분 안에](#4-첫-빌드--5분-안에)
- [5. 핵심 워크플로우: URL 한 줄로 전체 체인 추적](#5-핵심-워크플로우-url-한-줄로-전체-체인-추적)
- [6. CLI 명령 레퍼런스](#6-cli-명령-레퍼런스)
- [7. 프로젝트 타입별 가이드](#7-프로젝트-타입별-가이드)
- [8. 고급 사용](#8-고급-사용)
- [9. 정직한 한계 (알려진 미지원 케이스)](#9-정직한-한계-알려진-미지원-케이스)
- [10. 팀 공유 & CI 연동](#10-팀-공유--ci-연동)
- [11. 트러블슈팅](#11-트러블슈팅)
- [12. 기여 & 피드백](#12-기여--피드백)

---

## 0. 이 fork가 해결하는 문제

현대 웹앱에서 가장 흔한 AI 에이전트 질문은 대략 이런 형태입니다.

> "`/portal/agents/172` 페이지의 '편집' 버튼은 어떤 API를 호출하고, 그 API의 BE 로직은 어디 있나?"

이 질문에 답하려면 다음 체인 전체를 볼 수 있어야 합니다.

```
URL (/portal/agents/172)
 └─ FE 페이지 파일 (Next.js App Router 컨벤션)
    └─ 자식 컴포넌트 / 버튼 / onClick 핸들러
       └─ mutation hook · api-client 래퍼
          └─ 실제 fetch()
             └─ API URL 매칭
                └─ BE 라우트 핸들러 (Hono / Express / …)
                   └─ 서비스 · DB · 오류 발생 지점
```

업스트림 graphify는 **같은 언어 내부의 AST(import·call) 체인**까지는 정확히 추출합니다. 하지만:

- FE `fetch('/api/agents/:id/start')` ↔ BE `router.post('/agents/:id/start', …)` 사이의 **HTTP 경계 엣지가 자동으로 생기지 않음**
- **URL 자체가 그래프 노드로 모델링되지 않음** (Next.js의 `app/**/page.tsx` 컨벤션은 파일 시스템이 곧 라우팅)
- 호출 체인 추적용 **directed 역방향 질의**(`callers`/`callees`)가 없음

**이 fork v0.5.0은 위 세 가지를 정확히 추가합니다.** 의도적으로 LLM을 쓰지 않는 결정론적 경로로 동작하며, 기존 `/graphify` skill 파이프라인과 100% 호환됩니다.

### 0.5.2 업데이트 (2026-04-19)

Next.js·모노레포 실전 환경에서 v0.5.1까지 조용히 누락되던 두 종류의 엣지를 복구합니다. 코드 변경 없이 `pipx upgrade graphifyy` 후 `graphify update . --directed` 만 다시 돌리면 누락분이 채워집니다(AST 캐시 스키마가 v2로 올라가 자동 무효화됨).

- **tsconfig `paths` alias가 trailing block comment 때문에 무시되는 버그 수정**. v0.5.1의 JSONC 주석 제거 정규식이 문자열 값 안의 `/*`(예: `"@/*"`)를 블록 주석 시작으로 오해해 뒤에 오는 `*/`까지 통째로 삼켰습니다. 결과적으로 `paths` 딕셔너리 전체가 빈 채로 해석돼 `@/…` alias가 하나도 안 풀리고 `calls_http` 엣지가 대량으로 누락됐습니다. openclaw admin-portal에서 11건 → 수백 건으로 복구됨.
- **`import * as X from '…'` namespace import cross-file `calls` 엣지 생성**. `import * as authService from './auth-service'` + `authService.login(…)` 호출이 v0.5.1까지는 단순 last-segment 매칭으로 떨어져서 다른 파일의 동명 함수에 잘못 붙거나 아예 엣지가 안 생겼습니다. 이제 파일-scoped 심볼 조회로 정확히 해석됩니다(동일 파일에 동명 심볼 둘 이상이면 confidence 0.8로 downgrade). 구체적으로 openclaw의 `authService`/`agentService`/`auditLogService` 패턴 `callers` 질의가 0건 → 실제 사용량으로 복구됨.

---

## 1. 30초 요약 — 뭐가 다른가

| 기능 | 업스트림 | v0.5.0 fork |
|------|:---:|:---:|
| AST 기반 `imports`/`calls` 엣지 | ✅ | ✅ |
| 클러스터링·god nodes·Obsidian·HTML 시각화 | ✅ | ✅ |
| URL/Route를 first-class 노드로 | ❌ | ✅ (Next.js App/Pages Router) |
| BE 라우트 등록 자동 추출 (Hono) | ❌ | ✅ (cross-file mount 해석) |
| 래퍼-aware HTTP 호출 추출 (fetch/axios 체인) | ❌ | ✅ |
| tsconfig `paths` alias 해석 (`@/lib/...`) | 부분적 | ✅ |
| 방향 기반 역방향 질의 (`callers`/`callees`/`blast`) | ❌ | ✅ (DiGraph 전제) |
| 구체 URL로 페이지·API 검색 (`resolve`) | ❌ | ✅ |
| 라우트 오버레이 클러스터 분리 | — | ✅ (Leiden 왜곡 방지) |
| `--out-dir` 빌드 출력 리디렉션 | ❌ | ✅ |
| `init-ignore` 템플릿 생성 | ❌ | ✅ |

**새로 추가된 CLI 서브커맨드 6개**: `build`, `resolve`, `callers`, `callees`, `blast`, `init-ignore`. 추가로 기존 `update` 명령에 `--out-dir` / `--directed` 플래그가 추가되었습니다.

---

## 2. 이 도구가 내 프로젝트에 맞는가?

### ✅ 최적 케이스

- **Next.js + Hono** (openclaw-cloud 같은 구성) — 모든 기능 그대로 동작
- **Next.js + 어떤 TS/JS BE** — FE 오버레이는 완벽, BE는 Express/Fastify/NestJS 라우트 수동 추출 (2차 지원)
- **모노레포 (TS/JS)** — tsconfig paths 해석으로 alias import 정상 따라감

### 🟡 부분 동작

- **Python/Go/Rust/Java 등 단일 스택 프로젝트** — AST 기반 `callers`/`callees`/`blast`·클러스터링 전부 동작. 단 URL/API 오버레이는 생성되지 않음 (프레임워크별 라우트 추출 미지원)
- **Next.js + Python/Ruby/Go BE** — FE 오버레이는 동작, BE는 upstream AST만

### ❌ 현재 미지원

- 클라이언트 사이드만 있는 SPA(React/Vue 단독) — 서버 라우트가 없으므로 `/x` 체인이 절반만 잡힘. 클라이언트 FE 내부 호출 그래프는 여전히 동작.
- Rails/Django 전통 모놀리식 — BE 라우트 추출기 필요 (follow-up)

### 언어 지원 (AST 레벨, 업스트림과 동일)

Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, PowerShell, Elixir, Objective-C, Julia, Verilog, SystemVerilog, Vue, Svelte, Dart — 25개.

**판단 기준**: 당신이 구조 탐색/영향 분석/수정 범위 파악에 시간을 쓰고 있고, 특히 "이 URL이 어떻게 동작하나" 류 질문을 자주 한다면 유용합니다. 반대로 단일 파일/단일 함수 내부 버그 수정이 주력이라면 IDE 검색이 더 빠릅니다.

---

## 3. 설치

### 사전 요구사항

- Python 3.10 이상
- `pipx` (권장) 또는 `pip`
- git

`pipx`가 없다면:

```bash
# macOS
brew install pipx && pipx ensurepath
# Linux/WSL
python3 -m pip install --user pipx && python3 -m pipx ensurepath
# Windows (PowerShell)
python -m pip install --user pipx; python -m pipx ensurepath
```

### 메인 설치 (권장)

```bash
pipx install git+https://github.com/ceo-tw/graphify.git@v0.5.0
```

설치 확인:

```bash
graphify --help
# 첫 줄에 "Usage: graphify <command>" 가 나오고
# build, resolve, callers, callees, blast, init-ignore 가 목록에 있으면 성공
```

### 대안 설치 경로

**프로젝트 로컬 venv에 설치**:
```bash
python3 -m venv ~/.venvs/graphify
~/.venvs/graphify/bin/pip install git+https://github.com/ceo-tw/graphify.git@v0.5.0
# 호출할 때: ~/.venvs/graphify/bin/graphify ...
```

**개발/기여용 editable 설치**:
```bash
git clone https://github.com/ceo-tw/graphify.git
cd graphify
git checkout v0.5.0
pipx install --editable .
```

**브랜치 추적(최신 v4, 자주 갱신)**:
```bash
pipx install git+https://github.com/ceo-tw/graphify.git@v4
# 이후 최신화:
pipx reinstall graphifyy
```

### Claude Code 사용자 추가 단계

Claude Code에서 `/graphify` 스킬(업스트림 파이프라인)을 쓰려면:

```bash
graphify install
```

그리고 **Claude Code 새 세션을 엽니다.** 스킬은 세션 시작 시 로드되므로 실행 중인 세션은 업데이트되지 않습니다.

> ⚠️ 이전 버전 스킬이 설치돼 있으면 `warning: skill is from graphify X.Y.Z, package is 0.5.0. Run 'graphify install' to update.` 가 stderr로 표시됩니다. `graphify install`을 다시 돌리고 새 세션을 열면 사라집니다.

---

## 4. 첫 빌드 — 5분 안에

### 4.1 `.graphifyignore` 생성

어떤 폴더를 건드리지 말지 먼저 지정합니다. graphify가 프로젝트 타입을 감지해 적절한 기본값을 씁니다.

```bash
cd /path/to/your/project
graphify init-ignore .
```

생성된 `.graphifyignore` 예시 (일부):

```
node_modules/
.next/
dist/
build/
.venv/
__pycache__/
*.lock
*.map
.claude/architecture/graph/*/corpus/
.claude/architecture/graph/*/graphify-out/
graphify-out/
.vscode/
.idea/
.DS_Store
```

→ 필요에 맞게 편집하세요. 이 파일은 선택적으로 커밋합니다.

### 4.2 그래프 빌드 (LLM 무관, 완전 결정론적)

```bash
graphify build . --directed
```

- `--directed` 플래그는 **필수**입니다. `callers`/`callees`/`blast` 가 DiGraph를 요구합니다.
- 결과물은 `./graphify-out/` 에 생성됩니다.

출력 예시 (실제로 graphify 자체 레포에 돌린 결과):

```
[graphify watch] Rebuilt: 1774 nodes, 4015 edges, 29 communities
[graphify watch] graph.json, graph.html and GRAPH_REPORT.md updated in /path/to/project/graphify-out
Built: /path/to/project/graphify-out/graph.json
```

생성된 파일:

| 파일 | 용도 |
|------|------|
| `graphify-out/graph.json` | 모든 CLI 질의가 사용하는 입력 |
| `graphify-out/graph.html` | 브라우저에서 열어 시각적 탐색 |
| `graphify-out/GRAPH_REPORT.md` | god nodes, surprising connections, 제안 질문 |
| `graphify-out/graph.graphml` | Gephi·yEd 같은 외부 도구 연동 |

### 4.3 동작 확인 — 임의 노드로 질의

`callers`·`callees`·`blast` 는 대상을 **정확한 node id 또는 정확한 label** 로 받습니다. 퍼지 매치가 아닙니다. AST가 생성한 label에는 괄호가 포함되므로(`build_from_json()`) 주의하세요.

**방법 A — label로 질의 (괄호 포함, 따옴표로 감싸기)**:

```bash
graphify callers "build_from_json()" --edges calls --max-hops 2
```

**방법 B — node id 로 질의 (shell escape 필요 없음)**:

Python 함수의 id는 `_make_id(stem, name)` 형식입니다. stem이 `build` 이고 이름이 `build_from_json` 이면 id는 `build_build_from_json`.

```bash
graphify callers build_build_from_json --edges calls --max-hops 2
```

**id를 모를 때 — graph.json에서 찾기**:

```bash
jq '.nodes[] | select(.label | test("build_from_json"; "i")) | {id, label}' \
  graphify-out/graph.json
```

둘 중 어느 방법이든 `build()` 호출자, `_rebuild_code()` 호출자 등이 hop 거리와 함께 나열되면 성공입니다. "No node found matching …" 이 뜨면 대상이 label/id에 정확히 일치하지 않은 것이므로 위 jq 헬퍼로 실제 값을 확인하세요.

---

## 5. 핵심 워크플로우: URL 한 줄로 전체 체인 추적

이 섹션이 fork의 **존재 이유** 입니다.

### 시나리오

팀원이 다음을 보냅니다.

> "`https://local.app/portal/agents/172` 에서 '재시작' 버튼을 눌렀는데 500이 떠. 고쳐줘."

### Step 1 — URL → FE 페이지 매칭

```bash
graphify resolve /portal/agents/172 --json
```

출력(요약):
```json
{
  "url": "/portal/agents/172",
  "matches": [
    {
      "id": "url_portal_agents_id",
      "kind": "url",
      "url_pattern": "/portal/agents/:id",
      "source_file": "src/admin-portal/app/portal/agents/[id]/page.tsx",
      "neighbors": [
        { "relation": "renders", "label": "page.tsx", "id": "..." }
      ]
    }
  ]
}
```

→ `src/admin-portal/app/portal/agents/[id]/page.tsx` 파일이 이 URL을 렌더한다는 것이 즉시 확인됩니다.

### Step 2 — 페이지에서 호출하는 API 엔드포인트 나열

```bash
graphify callees <page-node-id> --edges calls,calls_http --max-hops 5
```

`callees`는 이 노드로부터 도달 가능한 모든 downstream 노드를 반환합니다. `calls_http` 관계가 있는 엔드포인트가 나오면 그게 버튼이 부르는 API입니다.

출력 예 (API 노드의 label은 `METHOD path` 형식 — 앞에 `API:` 접두사가 붙지 않음):
```
callees of page_agents_id: 12 node(s)
  hop=1  DetailActionBar [component_...] src/.../detail-action-bar.tsx
  hop=2  useAgentActions [hook_use_agent_actions] src/.../use-agent-actions.ts
  hop=3  POST /agents/:id/restart [api_post_agents_id_restart]
  ...
```

### Step 3 — API 엔드포인트 → BE 핸들러

API 노드는 `handled_by` 엣지로 BE 핸들러 함수에 연결돼 있습니다. 1-hop 질의 — label 또는 id 로 대상을 지정:

```bash
# label로 (정확히 일치해야 함, 앞에 API: 붙이지 않음)
graphify callees "POST /agents/:id/restart" --edges handled_by --max-hops 1
# 또는 id로 (공백/특수문자 escape 불필요)
graphify callees api_post_agents_id_restart --edges handled_by --max-hops 1
```

→ BE 핸들러 파일·라인이 반환됩니다.

### Step 4 — 핸들러의 내부 호출 체인

```bash
graphify blast <handler-node-id> --edges calls
```

출력 예:
```
blast_radius from restart_handler: 18 node(s), 6 file(s)
  admin-api/src/services/agent-manager.ts (4): start, stop, restart, getStatus
  admin-api/src/db/agents.ts (3): findById, updateStatus, logEvent
  ...
```

→ 이 핸들러를 바꾸면 영향받는 파일·함수 목록이 확정됩니다.

### Step 5 — 역방향: "이 함수를 누가 부르나?"

```bash
graphify callers <특정-함수> --edges calls --max-hops 3
```

500 오류의 원인이 된 함수에 대해 역추적. 테스트 파일을 제외하려면 출력을 grep으로 필터합니다.

### 이 체인의 가치

- 이전에는: 파일 찾기(rg) → import 추적 → string URL 수작업 매칭 → BE 코드 찾기. 5~10분.
- v0.5.0 이후: 4개 CLI 호출 또는 Claude에 URL만 넘기고 위 명령을 에이전트가 실행. 30초.

---

## 6. CLI 명령 레퍼런스

모든 JSON 출력은 stdout, 경고/진단은 stderr로 갑니다. 에이전트·스크립트 연동 시 `--json` + stdout 파이프가 안전합니다.

### `graphify build <source-root>`

결정론적(LLM 무관) 빌드. AST + Next.js routes + Hono routes + HTTP call-site 오버레이.

| 플래그 | 설명 |
|--------|------|
| `--directed` | DiGraph로 빌드 (`callers`/`callees`/`blast` 전제) |
| `--out-dir <dir>` | 기본 `<source-root>/graphify-out` 대신 다른 경로로 출력 |
| `--no-semantic` | 문서용 플래그 (이 CLI 경로는 항상 AST-only) |

예:
```bash
graphify build . --directed --out-dir ./.meta/graph
```

**업스트림 `/graphify` skill과의 차이**: skill은 문서/이미지/비디오까지 semantic pass로 처리. `build`는 코드·Next.js/Hono 라우트·HTTP 호출만. LLM 비용 없음.

### `graphify update <path>`

기존 `graphify-out/graph.json`을 증분 갱신. 코드 변경 후 재실행. 라벨은 `.graphify_labels.json`에서 복원되고, stale route/API 노드는 자동 pruning.

| 플래그 | 설명 |
|--------|------|
| `--directed` | (새) DiGraph로 재빌드 |
| `--out-dir <dir>` | (새) 출력 경로 재지정 |

### `graphify resolve <url> [--method METHOD] [--graph PATH] [--json]`

구체 URL에 매칭되는 `URL:*` 또는 `API:*` 오버레이 노드 + 1-hop 이웃 나열.

- `/portal/agents/172` → `/portal/agents/:id` 패턴 매칭
- `--method POST` → HTTP 메서드 필터
- Next.js 없는 프로젝트면 빈 결과 `{"matches": []}` — 정상

### `graphify callers <node> [--edges R1,R2] [--max-hops N] [--graph PATH] [--json]`

역방향 transitively 도달하는 노드(**upstream**) 나열. **DiGraph 필수** (`--directed`로 빌드).

- `--edges calls,calls_http` — `relation` 속성이 이 집합에 속하는 엣지만 추적
- `--max-hops 3` (기본값) — BFS 깊이 제한
- 노드 지정은 id 또는 label 둘 다 허용

### `graphify callees <node> [...]`

정방향 도달 가능한 노드(**downstream**). 플래그는 `callers`와 동일.

### `graphify blast <node> [--edges R1,R2] [--graph PATH] [--json]`

hop 제한 없는 downstream 전이 폐쇄. 파일별 그룹화된 결과를 반환.

출력 구조:
```json
{
  "target": "<node>",
  "nodes": [...],
  "by_file": { "src/foo.ts": ["id1", "id2"], ... },
  "total": 42
}
```

### `graphify init-ignore <project-path>`

`.graphifyignore` 파일이 없으면 프로젝트 구조 감지 후 sensible defaults 작성. 있으면 **줄 단위 equality**로 누락된 기본 패턴만 append (사용자 커스텀 유지).

### `graphify relabel <graphify-out-dir> [--labels labels.json]`

기존 `graph.json`을 재export. `labels.json`을 지정하면 커뮤니티 이름을 새로 부여. stale wiki 파일은 선제 삭제 후 재생성, graphml에도 라벨 반영.

---

## 7. 프로젝트 타입별 가이드

### 7.1 Next.js 14+ App Router + Hono BE (모노레포)

**예시 구조**:
```
my-app/
├── tsconfig.json                # paths: { "@/*": ["apps/web/src/*"] }
├── apps/
│   ├── web/                     # Next.js App Router
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── (auth)/
│   │   │   │   └── login/page.tsx
│   │   │   └── portal/agents/[id]/page.tsx
│   │   ├── lib/api-client.ts    # fetch wrapper — 자동 감지됨
│   │   └── hooks/use-agents.ts
│   └── api/
│       └── src/
│           ├── index.ts         # const app = new Hono(); app.route('/agents', agents)
│           └── routes/agents.ts # plans.get('/'), plans.post('/:id/start')
└── .graphifyignore
```

**빌드**:
```bash
cd my-app
graphify init-ignore .
graphify build . --directed
```

**기대 결과**:
- `URL:/portal/agents/:id` 노드 → `renders` → `apps/web/app/portal/agents/[id]/page.tsx`
- `API:POST /agents/:id/start` 노드 → `handled_by` → inline Hono handler (source_location 포함)
- FE의 `post('/agents/:id/start', ...)` → `calls_http POST` → `API:POST /agents/:id/start`

tsconfig `@/*` alias는 자동으로 해석됩니다.

### 7.2 Next.js + Express / Fastify / NestJS BE

FE 쪽은 동일하게 동작. BE 라우트 자동 추출은 **2차 지원** 상태이며 Hono만큼 완전하지는 않습니다. 대안:

1. **BE만 업스트림 skill로 추가 semantic pass**: `/graphify apps/api --mode deep` 로 Claude가 라우트 등록 패턴을 INFERRED 엣지로 추출.
2. 필요하다면 `.graphify/http-wrappers.json`에 수동 등록.

### 7.3 Next.js + 비-JS BE (Python/Go/Ruby 등)

FE 오버레이는 완벽히 동작합니다. BE 쪽은 업스트림 AST만 사용되므로 URL↔핸들러 엣지는 자동 생성되지 않습니다. 이 경우:

- FE → API URL 까지는 graphify가 커버 (`calls_http` 엣지)
- API → BE 핸들러 매칭은 수동 (URL 문자열을 키워드로 rg 검색)

### 7.4 단일 언어 프로젝트 (Python/Go/Rust/Java)

URL 오버레이는 생성되지 않지만 **AST 기반 impact 질의는 완전히 동작**합니다.

```bash
cd my-python-project
graphify build . --directed
graphify callers <특정 함수>
graphify blast <유틸 모듈>
```

특히 리팩토링·deprecation 작업에 유용:

```bash
graphify blast util_deprecated_helper --edges calls --json \
  | python -c 'import json,sys; d=json.load(sys.stdin); [print(f) for f in d["by_file"]]'
```

→ `deprecated_helper`를 사용하는 파일 목록을 바로 얻습니다.

### 7.5 모노레포 (TS 패키지 여러 개)

`tsconfig_paths.py`는 각 package 수준 `tsconfig.json`을 독립적으로 해석합니다:

- `apps/web/tsconfig.json` — `@/*` → `apps/web/src/*`
- `packages/shared/tsconfig.json` — `@shared/*` → `packages/shared/src/*`

특별 설정은 없습니다. `graphify build . --directed`로 끝.

---

## 8. 고급 사용

### 8.1 도메인별 분리 그래프 (`--out-dir`)

큰 프로젝트에서 도메인별 그래프를 나눠 관리:

```bash
# 전역 1장
graphify build . --directed --out-dir .meta/graph/_global/graphify-out

# 도메인별 (corpus 서브셋)
graphify build ./domains/audit-logs/corpus --directed \
  --out-dir .meta/graph/audit-logs/graphify-out
```

질의 시 `--graph` 플래그로 경로 지정:

```bash
graphify resolve /audit-logs/abc123 --json \
  --graph .meta/graph/_global/graphify-out/graph.json
```

### 8.2 API 래퍼 수동 등록

자동 감지에서 놓치는 래퍼 모듈은 `.graphify/http-wrappers.json`으로 지정:

```json
{
  "modules": {
    "@/services/custom-http": ["send", "request"],
    "./lib/legacy-api": ["legacyGet", "legacyPost"]
  }
}
```

파일 경로는 tsconfig paths로 해석되며, 상대 경로도 지원합니다.

### 8.3 라벨 영속화

첫 빌드 후 커뮤니티 이름을 의미있게 붙이고 싶다면:

1. `graphify-out/GRAPH_REPORT.md` 에서 커뮤니티별 god nodes를 확인
2. `.graphify_labels.json` 작성 (Claude 에이전트에 위임 가능):
   ```json
   {"0": "Authentication", "1": "Agent Runtime", "2": "Billing API"}
   ```
3. `graphify relabel graphify-out --labels .graphify_labels.json`
4. 이후 `graphify update`에도 라벨 유지됨 (baseline 기능, fork에서 강화)

### 8.4 증분 업데이트 워크플로우

개발 중 코드가 바뀌면:

```bash
graphify update . --directed
```

- AST 재추출 (코드 파일만)
- Next.js routes + Hono routes 재스캔
- 삭제된 파일의 URL/API 노드 자동 prune
- 라벨은 유지됨

느린 풀 리빌드를 피합니다.

### 8.5 JSON 출력 파이핑

모든 질의 명령은 `--json`을 지원합니다. 에이전트/스크립트 연동:

```bash
graphify callers listAuditLogs --edges calls,calls_http --json \
  | jq '.results[] | select(.source_file | contains("portal")) | .label'
```

### 8.6 시각화

`graphify-out/graph.html` 을 브라우저로 열면 됩니다. 로컬 서버 필요 없음. 커뮤니티별 색상·검색·필터·노드 클릭 시 사이드 패널에서 상세 정보.

도메인별 그래프를 분리했다면 각각 따로 엽니다.

---

## 9. 정직한 한계 (알려진 미지원 케이스)

아래는 테스트로 명시적으로 검증된 **미지원 케이스**입니다. 당신의 프로젝트가 여기 해당하면 부분적으로만 작동하거나, 해당 부분은 manual 검토가 필요합니다.

### 9.1 Hono 관련

| 패턴 | 상태 | 우회 |
|------|:---:|------|
| `app.route('/x', subRouter)` + `import subRouter from './foo'` | ✅ 지원 | — |
| 같은 파일 내 `app.route('/x', child)` + `const child = new Hono()` | ✅ 지원 | — |
| `const app = new Hono().basePath('/api')` 후 `app.get('/x', …)` | ⚠️ `/x`만 추출, `/api` 접두사 미결합 | 수동 재매핑 |
| `import { Hono as H } from 'hono'; const app = new H()` | ❌ 미탐지 | `import { Hono }` 로 리팩토링 |
| `app.route('/preferences', buildPreferencesApp(db))` (팩토리) | ❌ 미탐지 | 팩토리 대신 직접 Hono 인스턴스 export |
| `app.on(METHOD, '/x', handler)` | ❌ 의도적 제외 | `app.get/.post` 사용 |

### 9.2 Next.js 관련

| 패턴 | 상태 |
|------|:---:|
| Route groups `(auth)/login` → URL `/login` | ✅ |
| Dynamic segment `[id]` → `:id` | ✅ |
| Catch-all `[...slug]` → `*slug` (≥1 세그먼트) | ✅ |
| Optional catch-all `[[...slug]]` → 0 이상 세그먼트 | ✅ |
| Intercepting prefix `(.)photo` → `/photo` + intercepting flag | ✅ |
| Parallel routes `@modal` | ⚠️ 부분 — URL에 영향 없으나 노드 중복 제거 시 일부 메타 손실 |
| Pages Router `pages/**` | ✅ 기본 패턴 |

### 9.3 HTTP 호출 추출

| 패턴 | 상태 |
|------|:---:|
| `post('/x', body)` (래퍼 named import) | ✅ |
| `apiClient.get('/x')` (default import + method) | ✅ |
| `` post(`/users/${id}/reset`) `` (템플릿 리터럴) | ✅ `:id` 정규화 |
| `'/users/' + userId + '/x'` (binary concat) | ✅ `:userId` 정규화 |
| `fetch(buildUrl(params))` (런타임 URL 구성) | ❌ |
| `apiClient.search(q)`, `apiClient.fetchMilestones()` (타입드 클라이언트 도메인 메서드) | ❌ 메서드 바디 분석 미지원 |
| `fetch('https://external.com/x')` | ❌ 의도적 skip (외부 URL) |

### 9.4 일반 제약

- **에러 원인 추론**: graphify는 정적 분석 도구. 런타임 오류 메시지·스택트레이스는 범위 밖. 에이전트가 별도로 받아야 함.
- **동적 dispatch**: 리플렉션·event bus·plugin registry는 추출 불가.
- **Community ID 안정성**: 코드 규모가 크게 바뀌면 Leiden 커뮤니티 번호가 재정렬될 수 있음. cid 키 기반 라벨(`{"0": "...", "1": "..."}`)은 이론상 깨질 수 있으나 실무에서는 대부분 안정. 크리티컬 케이스는 fingerprint 기반 키로 follow-up 예정.

---

## 10. 팀 공유 & CI 연동

### 10.1 팀 설치 표준화

팀 `README` 혹은 내부 문서에 한 줄 추가:

```bash
pipx install git+https://github.com/ceo-tw/graphify.git@v0.5.0 \
  && graphify install \
  && echo "Open a new Claude Code session to load the skill."
```

고정 태그(`@v0.5.0`) 사용 시 모든 팀원이 같은 버전. 새 릴리스가 나오면 태그만 바꿔 재설치.

### 10.2 `graphify-out` 커밋 여부

권장: **커밋하지 않음.**

- `.gitignore`에 `graphify-out/` 추가
- CI 또는 pre-commit hook에서 자동 재빌드

이유: graph.json은 코드 스냅샷 파생물이라 diff가 크고 merge conflict 일으키기 쉬움. 대신 CI 아티팩트로 보관.

### 10.3 pre-commit 훅

업스트림 graphify의 `hook install` 사용 가능:

```bash
cd your-repo
graphify hook install
```

코드 파일 변경 시 자동으로 `graphify update`가 돌아 graph가 최신화됩니다. 코드-only 변경은 로컬에서 LLM 없이 동작.

### 10.4 CI (GitHub Actions 예)

```yaml
# .github/workflows/graph.yml
on:
  push: { branches: [main] }
jobs:
  build-graph:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install git+https://github.com/ceo-tw/graphify.git@v0.5.0
      - run: graphify build . --directed
      - uses: actions/upload-artifact@v4
        with:
          name: graphify-out
          path: graphify-out/
```

이 아티팩트를 내부 도구(Slack 봇, 대시보드 등)에서 다운로드해 공유합니다.

---

## 11. 트러블슈팅

### `graphify: command not found` (설치 후)

- **macOS/Linux (pipx)**: `pipx ensurepath` → 새 쉘 열기
- **Windows**: `%APPDATA%\Python\PythonXY\Scripts` 가 PATH에 있는지 확인. 없으면 `python -m graphify ...` 로 직접 호출
- **venv 설치**: `source ~/.venvs/graphify/bin/activate` 혹은 전체 경로 호출

### `warning: skill is from graphify X.Y.Z, package is 0.5.0` (Claude Code)

→ `graphify install` 실행 후 **Claude Code 세션을 새로 엽니다**. 스킬은 세션 시작 시에만 로드됩니다. stderr로 출력되므로 `--json` 파이프는 영향받지 않습니다.

### `error: callers/callees/blast_radius require a directed graph`

→ 그래프가 무향입니다. `graphify build . --directed` 또는 `graphify update . --directed` 로 재빌드하세요. 기존 `graph.json`의 `"directed": false`면 역방향 질의가 의미 없어 거부됩니다.

### `error: unknown command 'build'`

설치된 버전이 0.5.0 미만입니다:
```bash
pipx uninstall graphifyy
pipx install git+https://github.com/ceo-tw/graphify.git@v0.5.0
```

### `tree-sitter` 관련 ImportError

```bash
pip install 'tree-sitter>=0.23.0' tree-sitter-typescript tree-sitter-javascript
# (pipx 환경이면) pipx inject graphifyy tree-sitter-typescript
```

### resolve가 항상 빈 결과

- Next.js 프로젝트가 아닙니다 → 정상 (URL 오버레이 없음)
- 또는 `app/` 디렉토리가 없습니다 → `pages/` Router인지 확인
- 빌드를 `--directed` 없이 돌렸을 수 있음 → 재빌드

### `calls_http` 엣지 수가 기대보다 훨씬 적음 / `callers` 가 0건

v0.5.1 이하에서는 두 가지 원인이 조용히 엣지를 누락시켰습니다 — 둘 다 v0.5.2에서 수정됨:

1. **tsconfig에 trailing block comment**: `paths: { "@/*": ["src/*"] }` 뒤에 `/* … */` 주석이 있으면 v0.5.1 JSONC 파서가 `paths` 딕셔너리를 통째로 날렸습니다 → `@/…` alias 해석 실패 → `calls_http` 엣지 대량 누락.
2. **`import * as X from '…'` namespace 호출**: v0.5.1까지는 `X.method()` 의 cross-file `calls` 엣지가 정확히 해석되지 않았습니다(동명 함수에 잘못 붙거나 누락). `authService`/`agentService` 같은 패턴을 많이 쓰면 `callers` 질의가 0건 근처로 떨어집니다.

대응: `pipx upgrade graphifyy` 후 `graphify update . --directed` 로 재빌드하세요. v0.5.2의 AST 캐시 스키마 bump(v2)가 v0.5.1 캐시 엔트리를 자동 무효화하므로 별도 `rm -rf graphify-out/cache` 는 필요 없습니다.

### `graph.json` 구조 직접 보기

```bash
python3 -c "
import json
d = json.load(open('graphify-out/graph.json'))
kinds = {}
for n in d['nodes']:
    ft = n.get('file_type','(none)')
    kinds[ft] = kinds.get(ft,0)+1
print('nodes:', len(d['nodes']), '| by file_type:', kinds)
print('directed:', d.get('directed'))
print('sample url nodes:', [n['label'] for n in d['nodes'] if n.get('kind')=='url'][:5])
"
```

### graphify-out이 자꾸 재스캔 대상에 들어감

루트 `.graphifyignore`에 이 두 줄이 있는지 확인:
```
graphify-out/
.claude/architecture/graph/*/graphify-out/
```

`graphify init-ignore .` 를 다시 돌리면 자동으로 append됩니다 (줄 단위 equality).

---

## 12. 기여 & 피드백

- **이슈**: https://github.com/ceo-tw/graphify/issues
- **업스트림 리베이스 정책**: 이 fork는 업스트림(safishamsi/graphify)의 중요 핫픽스를 정기적으로 리베이스합니다. 이슈 리포트 시 먼저 업스트림에 이미 보고됐는지 확인해주세요.
- **PR 환영**: 특히 BE 라우트 추출기(Express/Fastify/NestJS/Django/Rails), 팩토리 패턴 해석, tsconfig `extends` 지원 등이 우선순위입니다.

### 로컬 개발

```bash
git clone https://github.com/ceo-tw/graphify.git
cd graphify && git checkout v4
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest tests/ --ignore=tests/test_install.py
```

현재 522개 테스트가 통과합니다(v0.5.0 기준). 기여 시 새 기능은 `tmp_path` 기반 합성 fixture 테스트를 먼저 작성하고(TDD), 기존 테스트 green을 유지하세요.

---

## 부록 A — 명령 치트시트

```bash
# 첫 설치 (한 번만)
pipx install git+https://github.com/ceo-tw/graphify.git@v0.5.0
graphify install                              # Claude Code 사용자만
# → Claude Code 새 세션 오픈

# 새 프로젝트에서 (한 번)
cd <your-project>
graphify init-ignore .
graphify build . --directed

# 일상 질의 (<node>는 정확한 node id 또는 정확한 label — 퍼지 매치 아님)
# id 모를 때: jq '.nodes[] | select(.label | test("검색어"; "i")) | {id, label}' graphify-out/graph.json
graphify resolve /portal/agents/172 --json
graphify callers <node> --edges calls,calls_http --max-hops 3 --json
graphify callees <node> --edges calls --json
graphify blast <node> --edges calls --json

# 코드 변경 후
graphify update . --directed

# 도메인 분리
graphify build . --directed --out-dir .meta/graph/<domain>/graphify-out
graphify resolve <url> --graph .meta/graph/<domain>/graphify-out/graph.json
```

## 부록 B — 생성되는 노드/엣지 타입

### 노드 `kind`
- `url` — FE 페이지 URL 패턴 (`URL:/portal/agents/:id`)
- `api` — BE API 엔드포인트 (`API:POST /agents/:id/start`)
- `service` — 원격 서비스 anchor (`SERVICE:admin-api`, 프록시 타겟)
- (nontype code nodes는 `file_type=code`)

### 엣지 `relation` (이번 fork 추가분)
- `renders` — URL → FE 페이지 컴포넌트
- `wraps` — URL → layout.tsx
- `loads` — URL → loading.tsx
- `handles_error_for` — URL → error.tsx
- `handled_by` — API → BE 핸들러 함수
- `forwards_to` — 프록시 API → SERVICE anchor
- `calls_http` — FE 함수 → API (메서드 attr 포함)

기존 업스트림 관계(`imports`, `imports_from`, `calls`, `inherits`, `contains`, `uses`, `rationale_for`, `semantically_similar_to`, …) 는 그대로 유지됩니다.
