---
name: env-control
type: workflow
description: |
  통합 환경 관리 스킬. 로컬/스테이징 개발 환경 실행, OrbStack K8s 배포를 일괄 관리합니다.
  서브커맨드: local (OrbStack port-forward), local-docker (Docker PostgreSQL),
  stage (EKS port-forward), deploy (OrbStack K8s 배포), status (전체 상태).
  사용 시점: 'local start', 'local stop', 'stage start', 'deploy api', 'dev status' 등.
  /env-control 커맨드로 호출.
argument-hint: "local [start|stop|restart|status] | local-docker [start|stop|restart <service>|status] | stage [start|stop|restart|status] | deploy [api|portal|billing|minio|all|status] | status"
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Glob
user-invocable: true
---

# env-control Skill

통합 환경 관리. 5개 서브커맨드로 로컬/스테이징/배포를 관리합니다.

---

## Common Conventions

- `<project-root>` = git repository root
- 모든 OrbStack kubectl 명령: `export PATH="$HOME/.orbstack/bin:$PATH"`
- 모든 백그라운드 프로세스: `run_in_background: true`, `timeout: 600000`
- 상태 보고 시 반드시 실제 `curl`/`lsof` 명령으로 확인. 캐시된 결과 재사용 금지.
- admin-api는 admin-portal보다 먼저 시작해야 함 (portal이 api에 프록시)

---

## 1. `local` -- OrbStack K8s Port-Forward

OrbStack K8s 클러스터의 admin-api, billing-api를 port-forward하고, admin-portal을 localhost에서 실행.

### Architecture

```
localhost:3001  ->  admin-portal (npm run dev, Next.js)
localhost:3002  ->  port-forward -> svc/admin-api:3000  (clawpod namespace)
localhost:3003  ->  port-forward -> svc/billing-api:3001 (clawpod namespace)
```

admin-portal `.env.local`: `ADMIN_API_URL=http://localhost:3002`, `BILLING_API_URL=http://localhost:3003`.

### Arguments

| Arg | Action |
|-----|--------|
| `start` (default) | 모든 서비스 시작 |
| `stop` | 포트 3001, 3002, 3003 kill |
| `restart` | stop -> 2s wait -> start |
| `status` | 포트 사용 및 health check |

### Start Pipeline

**Step 1: Kill Existing Processes**

```bash
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:3002 | xargs kill -9 2>/dev/null || true
lsof -ti:3003 | xargs kill -9 2>/dev/null || true
sleep 1
```

**Step 2: Verify OrbStack K8s**

```bash
export PATH="$HOME/.orbstack/bin:$PATH"
kubectl config current-context
kubectl get pods -n clawpod --no-headers | grep -E "admin-api|billing-api"
```

Pod이 Running 아니면 사용자에게 알리고 중단.

**Step 3: Start Port-Forwards (Background, parallel)**

```bash
# admin-api port-forward (run_in_background: true)
export PATH="$HOME/.orbstack/bin:$PATH"
kubectl port-forward svc/admin-api 3002:3000 -n clawpod

# billing-api port-forward (run_in_background: true)
export PATH="$HOME/.orbstack/bin:$PATH"
kubectl port-forward svc/billing-api 3003:3001 -n clawpod
```

**Step 4: Start admin-portal (Background)**

```bash
sleep 2 && cd <project-root>/src/admin-portal && npm run dev
```

**Step 5: Health Check** (5s wait)

```bash
curl -s -o /dev/null -w "admin-api: HTTP %{http_code}" http://localhost:3002/health 2>/dev/null || echo "admin-api: not reachable"
curl -s -o /dev/null -w "billing-api: HTTP %{http_code}" http://localhost:3003/health 2>/dev/null || echo "billing-api: not reachable"
curl -s -o /dev/null -w "admin-portal: HTTP %{http_code}" http://localhost:3001 2>/dev/null || echo "admin-portal: not reachable"
```

### Stop Pipeline

```bash
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:3002 | xargs kill -9 2>/dev/null || true
lsof -ti:3003 | xargs kill -9 2>/dev/null || true
sleep 2 && lsof -i:3001 -i:3002 -i:3003 -P 2>/dev/null || echo "All ports cleared"
```

### Status

```bash
echo "=== Port Status ==="
lsof -i:3001 -i:3002 -i:3003 -P -n 2>/dev/null || echo "No services on ports 3001/3002/3003"

echo "=== Health Checks ==="
curl -s -o /dev/null -w "admin-api (3002): HTTP %{http_code}\n" http://localhost:3002/health 2>/dev/null || echo "admin-api (3002): not running"
curl -s -o /dev/null -w "billing-api (3003): HTTP %{http_code}\n" http://localhost:3003/health 2>/dev/null || echo "billing-api (3003): not running"
curl -s -o /dev/null -w "admin-portal (3001): HTTP %{http_code}\n" http://localhost:3001 2>/dev/null || echo "admin-portal (3001): not running"

echo "=== OrbStack Pods ==="
export PATH="$HOME/.orbstack/bin:$PATH"
kubectl get pods -n clawpod --no-headers 2>/dev/null | grep -E "admin-api|billing-api" || echo "OrbStack pods not found"
```

---

## 2. `local-docker` -- Docker PostgreSQL Local Dev

Docker Desktop PostgreSQL을 사용하여 admin-api, admin-portal, showcase를 로컬에서 실행.

### Arguments

| Arg | Action |
|-----|--------|
| `start` | DB check -> admin-api -> admin-portal -> showcase |
| `stop` | 포트 3001, 3002, 3200 kill (PostgreSQL Docker는 유지) |
| `restart` | 전체 restart. Per-service: `restart api`, `restart portal`, `restart showcase`, `restart api, portal` |
| `status` | 실행 상태 확인 |
| (none) | 사용법 표시 |

### Configuration

환경 변수는 각 서비스의 `.env.local` 파일에서 읽음.

| Key | Source |
|-----|--------|
| admin-api | `src/admin-api/.env.local` (PORT, DATABASE_URL, JWT_SECRET, AI_PROVIDER, ANTHROPIC_API_KEY) |
| admin-portal | `src/admin-portal/.env.local` (PORT, HOSTNAME, ADMIN_API_URL) |
| showcase | port 3200, `npm run dev` |
| PostgreSQL | Docker Desktop container, port 5432 |

### Start Pipeline

**Step 1: Check Docker PostgreSQL**

```bash
/usr/local/bin/docker ps --format '{{.Names}}\t{{.Ports}}' 2>/dev/null | grep -i postgres
```

없으면 사용자에게 알리고 중단.

**Step 2: Ensure Database Exists**

```bash
/usr/local/bin/docker exec <container-name> psql -U postgres -lqt 2>/dev/null | grep openclaw_local
```

없으면: `/usr/local/bin/docker exec <container-name> psql -U postgres -c "CREATE DATABASE openclaw_local;"`

**Step 3: Kill Conflicting Ports**

```bash
lsof -ti :3002 | xargs kill -9 2>/dev/null || true
lsof -ti :3001 | xargs kill -9 2>/dev/null || true
lsof -ti :3200 | xargs kill -9 2>/dev/null || true
sleep 2
```

**Step 4: Start admin-api (Background)**

```bash
cd <project-root>/src/admin-api && \
set -a && source .env.local && set +a && \
npm run dev 2>&1
```

5초 후 health check: `curl -s http://localhost:3002/health`

**Step 5: Seed Test Users (First Run Only)**

```bash
/usr/local/bin/docker exec <container-name> psql -U postgres -d openclaw_local -c "SELECT count(*) FROM users;" 2>&1
```

count 0이면: `cd <project-root>/src/admin-api && set -a && source .env.local && set +a && npx tsx src/db/seed-users.ts` (timeout: 15000)

**Step 6: Start admin-portal (Background)**

```bash
cd <project-root>/src/admin-portal && \
set -a && source .env.local && set +a && \
npm run dev 2>&1
```

8초 후 verify: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3001` (200 or 307)

**Step 6.5: Start showcase (Background, parallel with portal)**

```bash
cd <project-root>/(showcase) && npm run dev 2>&1
```

5초 후 verify: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3200`

**Step 7: Open Showcase** -- `open http://localhost:3200`

**Step 8: Report**

```
| Service | URL | Status |
|---------|-----|--------|
| PostgreSQL | localhost:5432 | Running / Not Running |
| admin-api | http://localhost:3002 | Running / Failed |
| admin-portal | http://localhost:3001 | Running / Failed |
| showcase | http://localhost:3200 | Running / Failed |
```

Test accounts: `admin@example.com` / `Admin123!` (super_admin), `operator@example.com` / `Operator123!` (operator), `viewer@example.com` / `Viewer123!` (viewer)

### Per-Service Restart

- `restart api`: kill 3002 -> DB check -> start admin-api + seed
- `restart portal`: kill 3001 -> start admin-portal
- `restart showcase`: kill 3200 -> start showcase
- `restart api, portal`: kill 3001+3002 -> start api, then portal

### Stop Pipeline

```bash
lsof -ti :3001 | xargs kill -9 2>/dev/null || true
lsof -ti :3002 | xargs kill -9 2>/dev/null || true
lsof -ti :3200 | xargs kill -9 2>/dev/null || true
sleep 2 && lsof -i :3001 -i :3002 -i :3200 -P 2>/dev/null
```

PostgreSQL Docker 컨테이너는 절대 중지하지 않음 (공유 리소스).

### Status

```bash
lsof -i :3001 -i :3002 -i :3200 -P 2>/dev/null
curl -s http://localhost:3002/health 2>/dev/null || echo "admin-api: not running"
curl -s -o /dev/null -w "admin-portal: HTTP %{http_code}" http://localhost:3001 2>/dev/null || echo "admin-portal: not running"
curl -s -o /dev/null -w "showcase: HTTP %{http_code}" http://localhost:3200 2>/dev/null || echo "showcase: not running"
/usr/local/bin/docker ps --format '{{.Names}}\t{{.Status}}' 2>/dev/null | grep -i postgres
```

---

## 3. `stage` -- EKS Staging Port-Forward

EKS port-forward를 통해 스테이징 환경을 로컬에서 실행. socat Pod(RDS proxy), kubectl proxy, port-forward 3개(PostgreSQL, NATS, Redis), admin-api, admin-portal 관리.

### Convenience Variables

```
KCTX="arn:aws:eks:ap-northeast-2:331690203723:cluster/clawpod-prod"
KNS="clawpod"
```

모든 kubectl 명령: `--context $KCTX -n $KNS`

### Arguments

| Arg | Action |
|-----|--------|
| `start` | socat Pod -> kubectl proxy -> port-forward -> admin-api -> admin-portal |
| `stop` | services -> port-forward -> socat Pod 삭제 |
| `restart` | stop -> 3s wait -> start |
| `status` | 전체 컴포넌트 상태 확인 |
| (none) | 사용법 표시 |

### Scope

| Resource | Managed | Note |
|----------|:---:|------|
| admin-api (port 3000), admin-portal (port 3001) | O | Local Node.js |
| kubectl proxy (port 8001) | O | K8s API access |
| socat Pod (pg-tunnel) | O | 이 스킬이 생성/삭제 |
| port-forward (5432, 4222, 8080, 6379) | O | kubectl processes |
| PostgreSQL (RDS), NATS, Redis (EKS) | X | 공유 리소스 -- 절대 touch 금지 |
| Docker PostgreSQL | X | local-docker 스킬 소관 |

### Start Pipeline

**Step 1: Check Port 5432 Conflict**

```bash
lsof -i :5432 -P 2>/dev/null
```

사용 중이면 사용자에게 안내 후 중단. 프로세스를 kill하지 않음.

**Step 2: Parse RDS Endpoint**

```bash
grep '^DATABASE_URL=' <project-root>/src/admin-api/.env.staging | sed -E 's|.*@([^:]+):.*|\1|'
```

**Step 3: Create socat Proxy Pod**

기존 Pod 확인: `kubectl --context $KCTX -n $KNS get pod pg-tunnel --no-headers 2>/dev/null`

Running이면 skip. 아니면 삭제 후 재생성.

RDS endpoint는 ExternalName 서비스에서 조회:
```bash
kubectl --context $KCTX -n $KNS get svc postgresql -o jsonpath='{.spec.externalName}' 2>/dev/null
```

Pod 생성:
```bash
kubectl --context $KCTX -n $KNS run pg-tunnel --image=alpine/socat --restart=Never -- TCP-LISTEN:5432,fork,reuseaddr TCP:<RDS_ENDPOINT>:5432
kubectl --context $KCTX -n $KNS wait --for=condition=Ready pod/pg-tunnel --timeout=30s
```

**Step 4: Start kubectl proxy (Background)**

```bash
kubectl --context $KCTX proxy --port=8001
```

Verify: `curl -s http://localhost:8001/api/v1/namespaces/$KNS/pods?limit=1 | head -5`

**Step 5: Start Port-Forwards (Background, parallel)**

```bash
# PostgreSQL via socat
kubectl --context $KCTX -n $KNS port-forward pod/pg-tunnel 5432:5432

# NATS
kubectl --context $KCTX -n $KNS port-forward svc/nats-client 4222:4222 8080:8080

# Redis
kubectl --context $KCTX -n $KNS port-forward svc/redis 6379:6379
```

3초 후 verify: `lsof -i :5432 -i :4222 -i :8080 -i :6379 -P 2>/dev/null`

**Step 6: Start admin-api (Background)**

```bash
cd <project-root>/src/admin-api && npm run dev:staging 2>&1
```

5초 후 verify: `curl -s http://localhost:3000/health`

**Step 7: Start admin-portal (Background)**

```bash
cd <project-root>/src/admin-portal && npm run dev:staging 2>&1
```

8초 후 verify: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3001` (200 or 307)

### Stop Pipeline

```bash
# Step 1: Kill applications
lsof -ti :3001 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true

# Step 2: Kill kubectl proxy + port-forwards
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
lsof -ti :5432 | xargs kill -9 2>/dev/null || true
lsof -ti :4222 | xargs kill -9 2>/dev/null || true
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
lsof -ti :6379 | xargs kill -9 2>/dev/null || true

# Step 3: Delete socat Pod
kubectl --context $KCTX -n $KNS delete pod pg-tunnel --ignore-not-found 2>&1

# Step 4: Verify
sleep 2 && lsof -i :3000 -i :3001 -i :8001 -i :5432 -i :4222 -i :8080 -i :6379 -P 2>/dev/null
kubectl --context $KCTX -n $KNS get pod pg-tunnel --no-headers 2>/dev/null || echo "pg-tunnel Pod deleted"
```

### Status

```bash
lsof -i :3000 -i :3001 -P 2>/dev/null
lsof -i :8001 -P 2>/dev/null
lsof -i :5432 -i :4222 -i :8080 -i :6379 -P 2>/dev/null
curl -s http://localhost:8001/api/v1/namespaces/$KNS/pods?limit=1 2>/dev/null | head -3 || echo "kubectl proxy: not running"
curl -s http://localhost:3000/health 2>/dev/null || echo "admin-api: not running"
curl -s -o /dev/null -w "admin-portal: HTTP %{http_code}" http://localhost:3001 2>/dev/null || echo "admin-portal: not running"
kubectl --context $KCTX -n $KNS get pod pg-tunnel --no-headers 2>/dev/null || echo "pg-tunnel: not found"
```

---

## 4. `deploy` -- OrbStack K8s Deployment

OrbStack 로컬 K8s 환경에 서비스를 빌드하고 배포.

### Prerequisites

```bash
export PATH="$HOME/.orbstack/bin:$PATH"
CURRENT_CTX=$(kubectl config current-context 2>/dev/null)
if [[ "$CURRENT_CTX" != *"orbstack"* ]]; then
  echo "ERROR: kubectl context가 OrbStack이 아닙니다: $CURRENT_CTX"
  exit 1
fi
CTX="--context $CURRENT_CTX"
```

### Arguments

| Arg | Action |
|-----|--------|
| `status` | Pod, Service, Job, Ingress 조회 (빌드/배포 없음) |
| `minio` | MinIO 배포 (kubectl apply only) |
| `api` | Admin API 빌드 + 배포 |
| `portal` | Admin Portal 빌드 + 배포 |
| `billing` | Billing API 빌드 + 배포 |
| `all` | 순서대로 전체 배포: minio -> billing -> api -> portal |

### `deploy status`

```bash
kubectl $CTX get pods -n clawpod -o wide
kubectl $CTX get svc -n clawpod
kubectl $CTX get jobs -n clawpod
kubectl $CTX get ingress -n clawpod 2>/dev/null || true
```

### `deploy minio`

1. `kubectl $CTX delete job minio-init-bucket -n clawpod --ignore-not-found=true`
2. `kubectl $CTX apply -k orbstack/k8s/minio-dev/`
3. `kubectl $CTX wait --for=condition=ready pod -l app=minio -n clawpod --timeout=120s`
4. Health: `kubectl $CTX exec deploy/minio -n clawpod -- curl -sf http://localhost:9000/minio/health/live`
5. `kubectl $CTX wait --for=condition=complete job/minio-init-bucket -n clawpod --timeout=120s`

### `deploy api`

1. `docker build -t clawpod/admin-api:local -f "$PROJECT_ROOT/orbstack/dockerfiles/admin-api.Dockerfile" "$PROJECT_ROOT"`
2. `kubectl $CTX apply -k orbstack/k8s/admin-api-dev-https/`
3. `kubectl $CTX rollout restart deployment/admin-api -n clawpod`
4. `kubectl $CTX rollout status deployment/admin-api -n clawpod --timeout=180s`
5. Health: `kubectl $CTX exec deploy/admin-api -n clawpod -- curl -sf http://localhost:3000/health`

### `deploy portal`

1. `docker build -t clawpod/admin-portal:local -f "$PROJECT_ROOT/orbstack/dockerfiles/admin-portal.Dockerfile" "$PROJECT_ROOT/src/admin-portal/"`
2. `kubectl $CTX apply -k orbstack/k8s/admin-portal-dev-https/`
3. `kubectl $CTX rollout restart deployment/admin-portal -n clawpod`
4. `kubectl $CTX rollout status deployment/admin-portal -n clawpod --timeout=180s`

### `deploy billing`

1. `docker build -t clawpod/billing-api:local -f "$PROJECT_ROOT/orbstack/dockerfiles/billing-api.Dockerfile" "$PROJECT_ROOT"`
2. `kubectl $CTX apply -k orbstack/k8s/billing-api-dev-https/`
3. `kubectl $CTX rollout restart deployment/billing-api -n clawpod`
4. `kubectl $CTX rollout status deployment/billing-api -n clawpod --timeout=180s`

### `deploy all`

배포 순서 (의존성 기반): minio -> billing -> api -> portal

### Deploy URLs

- Portal: `https://local.clawpod.cloud`
- API health: `curl -sk https://local.clawpod.cloud/api/proxy/health`
- MinIO Console: `http://localhost:30901` (NodePort)
- MinIO API: `http://localhost:30900` (NodePort)

### Error Handling

| 상황 | 대응 |
|------|------|
| Docker 빌드 실패 | 에러 로그 출력, 중단 |
| Pod Ready 타임아웃 | `kubectl logs` + `kubectl describe pod` 출력 |
| Health check 실패 | Pod 로그 확인 후 보고 |
| context가 orbstack 아님 | 즉시 중단, context 전환 안내 |

---

## 5. `status` -- Combined Status Check

모든 환경의 상태를 한번에 확인.

```bash
echo "=== Local (OrbStack Port-Forward) ==="
lsof -i:3001 -i:3002 -i:3003 -P -n 2>/dev/null || echo "No local services"

echo ""
echo "=== Local (Docker) ==="
/usr/local/bin/docker ps --format '{{.Names}}\t{{.Status}}' 2>/dev/null | grep -i postgres || echo "Docker PostgreSQL: not running"
lsof -i:3200 -P -n 2>/dev/null || echo "Showcase: not running"

echo ""
echo "=== Staging ==="
lsof -i:3000 -i:8001 -i:5432 -i:4222 -i:6379 -P -n 2>/dev/null || echo "No staging services"

echo ""
echo "=== OrbStack K8s Pods ==="
export PATH="$HOME/.orbstack/bin:$PATH"
kubectl get pods -n clawpod -o wide 2>/dev/null || echo "OrbStack kubectl not available"
```

---

## Critical Rules

- PATH에 반드시 `$HOME/.orbstack/bin` 포함 (OrbStack 명령)
- 모든 백그라운드 프로세스: `run_in_background: true`, `timeout: 600000`
- 시작 전 반드시 기존 포트 프로세스 kill (포트 충돌 방지)
- admin-api가 admin-portal보다 먼저 시작 (프록시 의존성)
- health check는 반드시 실제 `curl`/`lsof` 실행. 캐시 재사용 금지.
- OrbStack Pod이 Running 아니면 사용자에게 알리고 중단
- staging의 socat Pod(`pg-tunnel`)은 stop 시 반드시 삭제 (EKS 리소스 정리)
- staging에서 port 5432 사용 중이면 kill하지 않고 사용자에게 안내
- Docker PostgreSQL 컨테이너는 절대 중지하지 않음 (공유 리소스)
- EKS staging kubectl: 반드시 `--context $KCTX -n $KNS` 사용
