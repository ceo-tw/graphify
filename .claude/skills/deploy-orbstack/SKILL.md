---
name: deploy-orbstack
type: workflow
description: "OrbStack 로컬 K8s 환경에 서비스를 배포합니다. api, portal, billing, minio, all, status 인자를 지원합니다. 사용 시점: (1) 코드 변경 후 OrbStack에 배포할 때, (2) 로컬 K8s Pod 상태를 확인할 때. /deploy-orbstack 커맨드로 호출."
argument-hint: "api | portal | billing | minio | all | status"
allowed-tools:
  - Bash
  - Read
  - Glob
user-invocable: true
---

# deploy-orbstack Skill

OrbStack 로컬 K8s 환경에 서비스를 빌드하고 배포합니다.

---

## 사전 조건

모든 배포 명령 실행 전, OrbStack PATH를 설정합니다:

```bash
export PATH="$HOME/.orbstack/bin:$PATH"
```

kubectl context가 orbstack인지 확인:

```bash
CURRENT_CTX=$(kubectl config current-context 2>/dev/null)
if [[ "$CURRENT_CTX" != *"orbstack"* ]]; then
  echo "ERROR: kubectl context가 OrbStack이 아닙니다: $CURRENT_CTX"
  exit 1
fi
CTX="--context $CURRENT_CTX"
```

---

## 인자별 동작

### `status`

Pod, Service, Job 상태를 조회합니다. 빌드나 배포 없이 조회만 수행.

```bash
kubectl $CTX get pods -n clawpod -o wide
kubectl $CTX get svc -n clawpod
kubectl $CTX get jobs -n clawpod
kubectl $CTX get ingress -n clawpod 2>/dev/null || true
```

---

### `minio`

MinIO (S3 호환 스토리지)를 배포합니다. Docker 빌드 없이 kubectl apply만 수행.

**단계:**

1. 기존 init Job 삭제 (Job은 immutable):
   ```bash
   kubectl $CTX delete job minio-init-bucket -n clawpod --ignore-not-found=true
   ```

2. Kustomize overlay 적용:
   ```bash
   kubectl $CTX apply -k orbstack/k8s/minio-dev/
   ```

3. Pod Ready 대기:
   ```bash
   kubectl $CTX wait --for=condition=ready pod -l app=minio -n clawpod --timeout=120s
   ```

4. Health check (MinIO API port 9000):
   ```bash
   kubectl $CTX exec deploy/minio -n clawpod -- curl -sf http://localhost:9000/minio/health/live
   ```

5. Init Job 완료 대기:
   ```bash
   kubectl $CTX wait --for=condition=complete job/minio-init-bucket -n clawpod --timeout=120s
   ```

6. 상태 보고:
   ```bash
   kubectl $CTX get pods -n clawpod -l app=minio -o wide
   kubectl $CTX get pods -n clawpod -l app=minio-init -o wide
   kubectl $CTX get svc minio -n clawpod
   ```

---

### `api`

Admin API를 빌드하고 배포합니다.

**단계:**

1. Docker 이미지 빌드:
   ```bash
   PROJECT_ROOT=$(git rev-parse --show-toplevel)
   docker build -t clawpod/admin-api:local \
     -f "$PROJECT_ROOT/orbstack/dockerfiles/admin-api.Dockerfile" \
     "$PROJECT_ROOT"
   ```

2. Kustomize overlay 적용:
   ```bash
   kubectl $CTX apply -k orbstack/k8s/admin-api-dev-https/
   ```

3. Rollout restart + 대기:
   ```bash
   kubectl $CTX rollout restart deployment/admin-api -n clawpod
   kubectl $CTX rollout status deployment/admin-api -n clawpod --timeout=180s
   ```

4. Health check:
   ```bash
   kubectl $CTX exec deploy/admin-api -n clawpod -- curl -sf http://localhost:3000/health
   ```

---

### `portal`

Admin Portal을 빌드하고 배포합니다.

**단계:**

1. Docker 이미지 빌드:
   ```bash
   PROJECT_ROOT=$(git rev-parse --show-toplevel)
   docker build -t clawpod/admin-portal:local \
     -f "$PROJECT_ROOT/orbstack/dockerfiles/admin-portal.Dockerfile" \
     "$PROJECT_ROOT/src/admin-portal/"
   ```

2. Kustomize overlay 적용:
   ```bash
   kubectl $CTX apply -k orbstack/k8s/admin-portal-dev-https/
   ```

3. Rollout restart + 대기:
   ```bash
   kubectl $CTX rollout restart deployment/admin-portal -n clawpod
   kubectl $CTX rollout status deployment/admin-portal -n clawpod --timeout=180s
   ```

---

### `billing`

Billing API를 빌드하고 배포합니다.

**단계:**

1. Docker 이미지 빌드:
   ```bash
   PROJECT_ROOT=$(git rev-parse --show-toplevel)
   docker build -t clawpod/billing-api:local \
     -f "$PROJECT_ROOT/orbstack/dockerfiles/billing-api.Dockerfile" \
     "$PROJECT_ROOT"
   ```

2. Kustomize overlay 적용:
   ```bash
   kubectl $CTX apply -k orbstack/k8s/billing-api-dev-https/
   ```

3. Rollout restart + 대기:
   ```bash
   kubectl $CTX rollout restart deployment/billing-api -n clawpod
   kubectl $CTX rollout status deployment/billing-api -n clawpod --timeout=180s
   ```

---

### `all`

모든 서비스를 순서대로 배포합니다.

**배포 순서** (의존성 기반):

1. `minio` -- 인프라 (S3 스토리지, api가 의존)
2. `billing` -- billing-api
3. `api` -- admin-api (MinIO, billing에 의존)
4. `portal` -- admin-portal (api에 의존)

각 단계는 위 개별 섹션의 절차를 그대로 따릅니다.

---

## 에러 처리

| 상황 | 대응 |
|------|------|
| Docker 빌드 실패 | 에러 로그 출력, 중단 |
| Pod Ready 타임아웃 | `kubectl logs` + `kubectl describe pod` 출력 |
| Health check 실패 | Pod 로그 확인 후 보고 |
| context가 orbstack 아님 | 즉시 중단, context 전환 안내 |

---

## 배포 완료 보고

배포 완료 시 다음 정보를 출력합니다:

- 배포된 서비스 목록
- Pod 상태 (`kubectl get pods -n clawpod`)
- 접속 URL:
  - Portal: `https://local.clawpod.cloud`
  - API health: `curl -sk https://local.clawpod.cloud/api/proxy/health`
  - MinIO Console: `http://localhost:30901` (NodePort)
  - MinIO API: `http://localhost:30900` (NodePort)
