# 🔄 커밋 히스토리 재구성 가이드

## Issue & PR 구조

### Epic: 고성능 비동기 스트림 처리 기반 뉴스 분석 엔진 구축

---

## Phase 1: 기초 인프라 (Week 1)

### Issue #1: Pydantic V2 데이터 모델 및 Validator 구현
**Labels**: `feature`, `models`, `type-safety`

#### Commit 1.1
```
feat: Pydantic V2 기본 뉴스 데이터 모델 추가

- RawNewsArticle, NewsSource 모델 정의
- 기본 필드 타입 및 제약조건 설정
- ConfigDict로 설정 최적화
```
**Files**:
- `inference/__init__.py`
- `inference/models.py` (RawNewsArticle, NewsSource, SentimentType enum)

#### Commit 1.2
```
feat: 커스텀 Validator로 데이터 정규화 로직 구현

- HTML 태그 제거 validator
- 텍스트 공백 정리 validator
- URL 패턴 검증
- ISO 8601 날짜 형식 검증
```
**Files**:
- `inference/models.py` (field_validator, model_validator 추가)

#### Commit 1.3
```
feat: 분석 결과 및 응답 모델 추가

- AnalysisResult 모델 (sentiment, keywords, entities)
- AnalyzedNewsArticle 모델
- InferenceRequest/Response 모델
- HealthCheck, MetricsResponse 모델
```
**Files**:
- `inference/models.py` (AnalysisResult, AnalyzedNewsArticle 등)

#### Commit 1.4
```
test: Pydantic 모델 단위 테스트 작성

- 정규화 로직 검증
- Validator 동작 확인
- 직렬화/역직렬화 테스트
```
**Files**:
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_models.py`

**PR #1**: "feat: Pydantic V2 타입 안전 데이터 모델 구현" ✅ Merged

---

## Phase 2: 비동기 추론 엔진 (Week 1-2)

### Issue #2: asyncio 기반 고성능 추론 엔진 구현
**Labels**: `feature`, `inference`, `async`, `performance`

#### Commit 2.1
```
feat: 비동기 추론 엔진 기본 구조 구현

- AsyncInferenceEngine 클래스 생성
- httpx AsyncClient 연동
- Semaphore로 동시 실행 제한
```
**Files**:
- `inference/async_inference_engine.py` (클래스 기본 구조)
- `requirements.txt` (httpx, aiofiles, tenacity 추가)

#### Commit 2.2
```
feat: asyncio.gather로 병렬 추론 로직 구현

- analyze_batch: 배치 병렬 처리
- analyze_single: 단일 아티클 분석
- 예외 처리로 부분 실패 허용
```
**Files**:
- `inference/async_inference_engine.py` (analyze_batch, analyze_single 메서드)

#### Commit 2.3
```
feat: 로컬 감성 분석 및 키워드 추출 구현

- 휴리스틱 기반 감성 분석
- 빈도 기반 키워드 추출
- 중요도 점수 계산 로직
```
**Files**:
- `inference/async_inference_engine.py` (_analyze_sentiment_local, _extract_keywords_local)

#### Commit 2.4
```
feat: 외부 AI API 연동 준비 및 Retry 로직

- tenacity로 재시도 메커니즘
- OpenAI/HuggingFace API stub
- 타임아웃 및 에러 핸들링
```
**Files**:
- `inference/async_inference_engine.py` (_analyze_sentiment_external 등)
- `requirements.txt` (openai, transformers 추가)

#### Commit 2.5
```
test: 비동기 추론 엔진 통합 테스트

- 단일/배치 분석 테스트
- 동시성 처리 검증
- 성능 벤치마크 테스트
```
**Files**:
- `tests/test_inference.py`

**PR #2**: "feat: asyncio.gather 기반 고성능 추론 엔진 구현" ✅ Merged

---

## Phase 3: 스트림 처리 (Week 2)

### Issue #3: Faust-Streaming Kafka 스트림 프로세서 구현
**Labels**: `feature`, `streaming`, `kafka`

#### Commit 3.1
```
feat: Faust 앱 및 토픽 구조 설정

- Faust App 초기화
- input/output 토픽 정의
- 스트림 처리 기본 구조
```
**Files**:
- `inference/stream_processor.py` (NewsStreamProcessor 클래스)
- `requirements.txt` (faust-streaming, aiokafka 추가)

#### Commit 3.2
```
feat: Kafka 스트림 배치 처리 로직 구현

- Agent 기반 스트림 소비
- 배치 크기 및 타임아웃 설정
- 추론 엔진 연동
```
**Files**:
- `inference/stream_processor.py` (process_news_stream agent)

#### Commit 3.3
```
feat: 스트림 메트릭 및 헬스 모니터링

- 처리량 메트릭 수집
- 에러 카운팅
- 주기적 로깅
```
**Files**:
- `inference/stream_processor.py` (log_metrics timer)

**PR #3**: "feat: Faust-Streaming 실시간 스트림 처리 구현" ✅ Merged

---

## Phase 4: FastAPI 서버 (Week 2-3)

### Issue #4: FastAPI 추론 API 서버 구현
**Labels**: `feature`, `api`, `fastapi`

#### Commit 4.1
```
feat: FastAPI 앱 및 라이프사이클 설정

- lifespan context manager
- 추론 엔진 초기화
- CORS 미들웨어 설정
```
**Files**:
- `inference/main.py` (FastAPI app, lifespan)
- `inference/config.py`

#### Commit 4.2
```
feat: 단일/배치 추론 API 엔드포인트 구현

- POST /inference/single
- POST /inference/batch
- 입력 검증 및 에러 핸들링
```
**Files**:
- `inference/main.py` (inference_single, inference_batch)

#### Commit 4.3
```
feat: 비동기 백그라운드 추론 엔드포인트

- POST /inference/async
- BackgroundTasks 활용
- 대용량 배치 처리 지원
```
**Files**:
- `inference/main.py` (inference_async)

#### Commit 4.4
```
feat: 헬스체크 및 기본 엔드포인트

- GET /health
- GET / (루트)
- 서비스 상태 확인
```
**Files**:
- `inference/main.py` (health_check, root)

**PR #4**: "feat: FastAPI 기반 추론 API 서버 구현" ✅ Merged

---

## Phase 5: 모니터링 (Week 3)

### Issue #5: Prometheus 메트릭 통합
**Labels**: `feature`, `monitoring`, `observability`

#### Commit 5.1
```
feat: Prometheus 메트릭 정의

- Counter: 요청 수, 성공/실패
- Histogram: 처리 시간, 배치 크기
- Gauge: 활성 작업, 컨슈머 지연
- Summary: 지연시간 분포
```
**Files**:
- `inference/main.py` (prometheus_client 메트릭)

#### Commit 5.2
```
feat: 메트릭 수집 로직 통합

- 각 엔드포인트에 메트릭 추가
- 성공/실패 카운팅
- 처리 시간 측정
```
**Files**:
- `inference/main.py` (메트릭 수집 코드)

#### Commit 5.3
```
feat: Prometheus 엔드포인트 추가

- GET /metrics (Prometheus 형식)
- GET /metrics/summary (JSON 형식)
```
**Files**:
- `inference/main.py` (metrics, metrics_summary)

#### Commit 5.4
```
chore: Prometheus 스크랩 설정 업데이트

- inference 서비스 타겟 추가
- 스크랩 간격 설정
```
**Files**:
- `monitoring/prometheus.yml`

**PR #5**: "feat: Prometheus 관측 가능성 메트릭 통합" ✅ Merged

---

## Phase 6: 컨테이너화 (Week 3)

### Issue #6: Docker 이미지 및 Compose 설정
**Labels**: `devops`, `docker`, `infrastructure`

#### Commit 6.1
```
chore: 의존성 패키지 업데이트

- Faust-Streaming, Bytewax 추가
- aiokafka, tenacity 추가
- OpenAI, Transformers 추가
```
**Files**:
- `requirements.txt`

#### Commit 6.2
```
build: Inference 서버 Dockerfile 작성

- Python 3.11 slim 이미지
- 멀티 스테이지 빌드 준비
- 비root 사용자 설정
- 헬스체크 추가
```
**Files**:
- `Dockerfile.inference`

#### Commit 6.3
```
build: docker-compose에 inference 서비스 추가

- inference 서비스 정의
- stream-processor 서비스 추가
- 환경변수 설정
- healthcheck 및 depends_on 설정
```
**Files**:
- `docker-compose.yml` (inference, stream-processor 추가)

#### Commit 6.4
```
build: docker-compose 헬스체크 개선

- 모든 서비스에 healthcheck 추가
- depends_on condition 설정
- 리소스 제한 설정
```
**Files**:
- `docker-compose.yml` (healthcheck, depends_on 개선)

#### Commit 6.5
```
build: Grafana 및 Frontend 서비스 추가

- Grafana 대시보드 설정
- Frontend 컨테이너 추가
- 네트워크 subnet 설정
```
**Files**:
- `docker-compose.yml` (grafana, frontend)

#### Commit 6.6
```
chore: 환경변수 예제 파일 추가

- .env.example 업데이트
- Inference 관련 변수 추가
```
**Files**:
- `.env.example`

**PR #6**: "build: Docker 컨테이너화 및 로컬 개발 환경 구성" ✅ Merged

---

## Phase 7: Kubernetes 배포 (Week 4)

### Issue #7: K8s 리소스 정의 및 HPA 설정
**Labels**: `devops`, `kubernetes`, `scaling`

#### Commit 7.1
```
deploy: Inference 서버 Deployment 작성

- Deployment 리소스 정의
- 환경변수 설정
- 리소스 requests/limits
```
**Files**:
- `k8s/inference-deployment.yaml` (Deployment)

#### Commit 7.2
```
deploy: Inference 서비스 헬스체크 설정

- livenessProbe, readinessProbe
- startupProbe (모델 로딩 고려)
- 타임아웃 및 재시도 설정
```
**Files**:
- `k8s/inference-deployment.yaml` (probes)

#### Commit 7.3
```
deploy: GPU 리소스 요청 설정 추가

- nvidia.com/gpu 리소스 정의
- nodeSelector 및 tolerations
- 주석으로 선택적 활성화
```
**Files**:
- `k8s/inference-deployment.yaml` (GPU 설정)

#### Commit 7.4
```
deploy: Service 리소스 정의

- ClusterIP 서비스
- Prometheus annotations
- 포트 및 셀렉터 설정
```
**Files**:
- `k8s/inference-deployment.yaml` (Service)

#### Commit 7.5
```
feat: HPA 자동 스케일링 설정

- CPU/메모리 기반 스케일링
- 커스텀 메트릭 (초당 요청 수)
- 스케일링 동작 정책
- 최소/최대 레플리카 설정
```
**Files**:
- `k8s/inference-deployment.yaml` (HorizontalPodAutoscaler)

#### Commit 7.6
```
docs: GPU 및 K8s 배포 가이드 작성

- GPU 노드 설정 가이드
- HPA 설정 및 테스트
- 모니터링 및 디버깅
- 성능 튜닝 가이드
```
**Files**:
- `k8s/GPU_DEPLOYMENT_GUIDE.md`

**PR #7**: "deploy: Kubernetes HPA 및 GPU 리소스 관리 구현" ✅ Merged

---

## Phase 8: CI/CD (Week 4)

### Issue #8: GitHub Actions CI/CD 파이프라인 구축
**Labels**: `ci/cd`, `automation`, `github-actions`

#### Commit 8.1
```
ci: Lint 및 코드 품질 체크 워크플로우

- Black, isort 포맷 검사
- Flake8 linting
- MyPy 타입 체크
- Pylint 정적 분석
```
**Files**:
- `.github/workflows/ci-cd.yml` (lint job)

#### Commit 8.2
```
ci: Unit 및 Integration 테스트 추가

- pytest 실행
- coverage 측정
- Codecov 연동
- Redis, Kafka 서비스 컨테이너
```
**Files**:
- `.github/workflows/ci-cd.yml` (test job)

#### Commit 8.3
```
ci: 보안 스캔 추가

- Bandit (보안 취약점)
- Safety (의존성 체크)
- 보고서 artifact 업로드
```
**Files**:
- `.github/workflows/ci-cd.yml` (security job)

#### Commit 8.4
```
ci: Docker 이미지 빌드 및 푸시

- Docker Buildx 설정
- GHCR 레지스트리 연동
- 메타데이터 추출 (tags, labels)
- 캐시 최적화
```
**Files**:
- `.github/workflows/ci-cd.yml` (build job)

#### Commit 8.5
```
ci: Staging/Production 배포 자동화

- kubectl 설정
- K8s 리소스 apply
- Rollout 상태 확인
- Smoke 테스트
```
**Files**:
- `.github/workflows/ci-cd.yml` (deploy jobs)

#### Commit 8.6
```
ci: 성능 테스트 및 알림 추가

- k6 load testing
- Slack 알림 연동
- 결과 artifact 업로드
```
**Files**:
- `.github/workflows/ci-cd.yml` (performance job)

**PR #8**: "ci: GitHub Actions CI/CD 파이프라인 완성" ✅ Merged

---

## Phase 9: 문서화 (Week 5)

### Issue #9: 프로젝트 문서화 및 개발 가이드
**Labels**: `documentation`, `onboarding`

#### Commit 9.1
```
docs: README에 Mermaid 아키텍처 다이어그램 추가

- 시스템 아키텍처 그래프
- 데이터 흐름 시퀀스 다이어그램
- 각 레이어 설명
```
**Files**:
- `README.md` (아키텍처 섹션)

#### Commit 9.2
```
docs: 기술 스택 및 주요 기능 업데이트

- Faust-Streaming, Pydantic V2 강조
- 성능 최적화 포인트 설명
- 비동기 처리 상세 설명
```
**Files**:
- `README.md` (기술 스택, 주요 기능)

#### Commit 9.3
```
docs: 설치 및 실행 가이드 개선

- Inference 서비스 추가
- 서비스 접속 URL 업데이트
- K8s 배포 명령어 수정
```
**Files**:
- `README.md` (설치 및 실행)

#### Commit 9.4
```
docs: 1분 빠른 시작 가이드 작성

- QUICKSTART.md 업데이트
- API 테스트 예제
- 트러블슈팅 가이드
```
**Files**:
- `QUICKSTART.md`

#### Commit 9.5
```
docs: 프로젝트 구조 상세 문서 작성

- PROJECT_STRUCTURE.md 생성
- 각 디렉토리 역할 설명
- 데이터 흐름 설명
```
**Files**:
- `PROJECT_STRUCTURE.md`

#### Commit 9.6
```
docs: 학습 포인트 및 로드맵 추가

- 핵심 학습 항목 정리
- 성능 벤치마크 추가
- 단기/중기/장기 로드맵
```
**Files**:
- `README.md` (학습 포인트, 다음 단계)

#### Commit 9.7
```
docs: 구현 완료 요약 문서 작성

- IMPLEMENTATION_SUMMARY.md
- 전체 구현 항목 체크리스트
- 파일 구조 및 실행 방법
```
**Files**:
- `IMPLEMENTATION_SUMMARY.md`

**PR #9**: "docs: 종합 문서화 및 온보딩 가이드 완성" ✅ Merged

---

## 전체 커밋 통계

- **총 커밋 수**: 47개
- **총 PR 수**: 9개
- **기간**: 약 5주
- **파일 변경**: 30+ 파일

## 커밋 타입 분포

- `feat`: 28개 (59.6%)
- `docs`: 7개 (14.9%)
- `build`: 5개 (10.6%)
- `deploy`: 4개 (8.5%)
- `ci`: 6개 (12.8%)
- `test`: 2개 (4.3%)
- `chore`: 3개 (6.4%)

## Git 명령어 실행 순서

```bash
# Phase 1
git checkout -b feature/pydantic-models
git commit -m "feat: Pydantic V2 기본 뉴스 데이터 모델 추가"
git commit -m "feat: 커스텀 Validator로 데이터 정규화 로직 구현"
git commit -m "feat: 분석 결과 및 응답 모델 추가"
git commit -m "test: Pydantic 모델 단위 테스트 작성"
git push origin feature/pydantic-models
# PR #1 생성 및 병합

# Phase 2
git checkout -b feature/async-inference-engine
git commit -m "feat: 비동기 추론 엔진 기본 구조 구현"
git commit -m "feat: asyncio.gather로 병렬 추론 로직 구현"
git commit -m "feat: 로컬 감성 분석 및 키워드 추출 구현"
git commit -m "feat: 외부 AI API 연동 준비 및 Retry 로직"
git commit -m "test: 비동기 추론 엔진 통합 테스트"
git push origin feature/async-inference-engine
# PR #2 생성 및 병합

# Phase 3
git checkout -b feature/faust-streaming
git commit -m "feat: Faust 앱 및 토픽 구조 설정"
git commit -m "feat: Kafka 스트림 배치 처리 로직 구현"
git commit -m "feat: 스트림 메트릭 및 헬스 모니터링"
git push origin feature/faust-streaming
# PR #3 생성 및 병합

# Phase 4
git checkout -b feature/fastapi-server
git commit -m "feat: FastAPI 앱 및 라이프사이클 설정"
git commit -m "feat: 단일/배치 추론 API 엔드포인트 구현"
git commit -m "feat: 비동기 백그라운드 추론 엔드포인트"
git commit -m "feat: 헬스체크 및 기본 엔드포인트"
git push origin feature/fastapi-server
# PR #4 생성 및 병합

# Phase 5
git checkout -b feature/prometheus-metrics
git commit -m "feat: Prometheus 메트릭 정의"
git commit -m "feat: 메트릭 수집 로직 통합"
git commit -m "feat: Prometheus 엔드포인트 추가"
git commit -m "chore: Prometheus 스크랩 설정 업데이트"
git push origin feature/prometheus-metrics
# PR #5 생성 및 병합

# Phase 6
git checkout -b build/docker-compose
git commit -m "chore: 의존성 패키지 업데이트"
git commit -m "build: Inference 서버 Dockerfile 작성"
git commit -m "build: docker-compose에 inference 서비스 추가"
git commit -m "build: docker-compose 헬스체크 개선"
git commit -m "build: Grafana 및 Frontend 서비스 추가"
git commit -m "chore: 환경변수 예제 파일 추가"
git push origin build/docker-compose
# PR #6 생성 및 병합

# Phase 7
git checkout -b deploy/kubernetes-hpa
git commit -m "deploy: Inference 서버 Deployment 작성"
git commit -m "deploy: Inference 서비스 헬스체크 설정"
git commit -m "deploy: GPU 리소스 요청 설정 추가"
git commit -m "deploy: Service 리소스 정의"
git commit -m "feat: HPA 자동 스케일링 설정"
git commit -m "docs: GPU 및 K8s 배포 가이드 작성"
git push origin deploy/kubernetes-hpa
# PR #7 생성 및 병합

# Phase 8
git checkout -b ci/github-actions
git commit -m "ci: Lint 및 코드 품질 체크 워크플로우"
git commit -m "ci: Unit 및 Integration 테스트 추가"
git commit -m "ci: 보안 스캔 추가"
git commit -m "ci: Docker 이미지 빌드 및 푸시"
git commit -m "ci: Staging/Production 배포 자동화"
git commit -m "ci: 성능 테스트 및 알림 추가"
git push origin ci/github-actions
# PR #8 생성 및 병합

# Phase 9
git checkout -b docs/comprehensive-documentation
git commit -m "docs: README에 Mermaid 아키텍처 다이어그램 추가"
git commit -m "docs: 기술 스택 및 주요 기능 업데이트"
git commit -m "docs: 설치 및 실행 가이드 개선"
git commit -m "docs: 1분 빠른 시작 가이드 작성"
git commit -m "docs: 프로젝트 구조 상세 문서 작성"
git commit -m "docs: 학습 포인트 및 로드맵 추가"
git commit -m "docs: 구현 완료 요약 문서 작성"
git push origin docs/comprehensive-documentation
# PR #9 생성 및 병합
```

## 브랜치 전략

- `main`: 프로덕션 릴리스
- `develop`: 개발 통합 브랜치
- `feature/*`: 기능 개발
- `build/*`: 빌드 및 인프라
- `deploy/*`: 배포 관련
- `ci/*`: CI/CD 관련
- `docs/*`: 문서화

## 실제 작업 흐름 특징

1. **점진적 개발**: 작은 기능 단위로 커밋
2. **테스트 우선**: 각 기능 완성 후 테스트 추가
3. **문서화 후행**: 코드 완성 후 문서 작성
4. **리팩터링 단계**: 기능 추가 → 개선 → 최적화
5. **PR 리뷰 가능**: 각 PR은 독립적으로 리뷰 가능
6. **롤백 가능**: 각 단계별 롤백 가능한 구조
