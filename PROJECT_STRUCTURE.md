# 📚 프로젝트 구조

```
prj-py/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                 # GitHub Actions CI/CD 파이프라인
│
├── inference/                        # 🆕 고성능 비동기 추론 엔진
│   ├── __init__.py
│   ├── config.py                     # 추론 서버 설정
│   ├── models.py                     # Pydantic V2 모델 및 Validator
│   ├── async_inference_engine.py    # asyncio.gather 기반 추론 엔진
│   ├── stream_processor.py          # Faust-Streaming 프로세서
│   └── main.py                       # FastAPI 서버 진입점
│
├── consumer/
│   ├── __init__.py
│   ├── config.py
│   ├── kafka_consumer.py
│   ├── analyzer.py                   # 기존 분석 로직
│   ├── redis_storage.py
│   └── main.py
│
├── producer/
│   ├── __init__.py
│   ├── config.py
│   ├── kafka_producer.py
│   ├── news_client.py
│   └── main.py
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.vue
│       └── main.js
│
├── k8s/                              # Kubernetes 배포 설정
│   ├── namespace.yaml
│   ├── secret.yaml
│   ├── configmap.yaml
│   ├── kafka-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── producer-deployment.yaml
│   ├── consumer-deployment.yaml
│   ├── inference-deployment.yaml     # 🆕 추론 서버 배포
│   ├── hpa.yaml                      # Horizontal Pod Autoscaler
│   ├── GPU_DEPLOYMENT_GUIDE.md       # 🆕 GPU 리소스 가이드
│   └── README.md
│
├── monitoring/
│   ├── prometheus.yml                # Prometheus 설정 (inference 추가)
│   └── PROMETHEUS_GUIDE.md
│
├── tests/                            # 테스트 (추가 필요)
│   ├── test_inference.py
│   ├── test_models.py
│   └── test_stream_processor.py
│
├── Dockerfile.producer
├── Dockerfile.consumer
├── Dockerfile.inference              # 🆕 추론 서버 Dockerfile
├── docker-compose.yml                # 전체 환경 구성 (개선됨)
├── requirements.txt                  # Python 의존성 (업데이트됨)
├── .env.example
├── .gitignore
├── README.md                         # 🆕 Mermaid 다이어그램 포함
├── QUICKSTART.md                     # 🆕 1분 환경 구성 가이드
└── PROJECT_STRUCTURE.md              # 이 파일

```

## 🎯 핵심 컴포넌트

### 1. Inference Engine (`inference/`)

고성능 비동기 추론을 위한 핵심 모듈:

- **models.py**: Pydantic V2 모델
  - `RawNewsArticle`: 원본 뉴스 데이터
  - `AnalyzedNewsArticle`: 분석된 뉴스
  - `AnalysisResult`: 분석 결과
  - 커스텀 Validator로 데이터 정규화

- **async_inference_engine.py**: 비동기 추론 엔진
  - `asyncio.gather`로 다중 API 호출 병렬 처리
  - Semaphore로 rate limiting
  - Retry 메커니즘 (tenacity)
  - Connection pooling (httpx)

- **stream_processor.py**: Faust 스트림 프로세서
  - Kafka 스트림 실시간 소비
  - 배치 처리로 처리량 최적화
  - Stateful 처리 지원

- **main.py**: FastAPI 서버
  - `/inference/single`: 단일 뉴스 분석
  - `/inference/batch`: 배치 분석
  - `/metrics`: Prometheus 메트릭
  - `/health`: 헬스체크

### 2. Producer (`producer/`)

뉴스 데이터 수집 및 Kafka 전송

### 3. Consumer (`consumer/`)

Kafka에서 뉴스 소비 및 실시간 분석

### 4. Frontend (`frontend/`)

Vue.js 3 기반 실시간 대시보드

### 5. K8s (`k8s/`)

Kubernetes 배포 설정:
- GPU 리소스 관리
- HPA (Horizontal Pod Autoscaler)
- Pod Disruption Budget
- Network Policies

### 6. Monitoring (`monitoring/`)

Prometheus 기반 모니터링:
- 추론 성공률
- 처리 지연시간
- Kafka 컨슈머 지연
- 활성 작업 수

## 📊 데이터 흐름

```
News API → Producer → Kafka → Faust Processor
                                     ↓
                          Async Inference Engine
                                     ↓
                          (asyncio.gather)
                          ↙        ↓        ↘
                    OpenAI   HuggingFace   Local
                          ↘        ↓        ↙
                                     ↓
                          Analyzed News → Redis
                                               ↓
                                         Frontend (WebSocket)
```

## 🔧 개발 가이드

### 로컬 개발

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env

# 3. Docker로 인프라 실행
docker-compose up -d kafka redis prometheus

# 4. 서비스 실행
python -m uvicorn inference.main:app --reload --port 8000
```

### 테스트

```bash
# Unit tests
pytest tests/ -v

# Coverage
pytest tests/ --cov=inference --cov-report=html

# Load testing
k6 run tests/load_test.js
```

### 코드 품질

```bash
# Formatting
black inference/ consumer/ producer/
isort inference/ consumer/ producer/

# Linting
flake8 inference/ consumer/ producer/
pylint inference/ consumer/ producer/

# Type checking
mypy inference/ --ignore-missing-imports
```

## 🚀 배포

### Docker Compose (로컬)

```bash
docker-compose up -d
```

### Kubernetes (프로덕션)

```bash
# 전체 배포
kubectl apply -f k8s/

# 특정 서비스만
kubectl apply -f k8s/inference-deployment.yaml
```

## 📈 성능 최적화

### 추론 엔진
- `MAX_CONCURRENT_REQUESTS`: 동시 요청 수 (기본 20)
- `BATCH_SIZE`: 배치 크기 (기본 10)
- `BATCH_TIMEOUT`: 배치 타임아웃 (기본 2초)

### Kafka
- `KAFKA_LOG_RETENTION_HOURS`: 로그 보관 기간
- `KAFKA_LOG_RETENTION_BYTES`: 로그 크기 제한

### Redis
- `maxmemory`: 최대 메모리 (기본 512MB)
- `maxmemory-policy`: 메모리 정책 (allkeys-lru)

## 🔗 관련 문서

- [README.md](README.md): 전체 프로젝트 개요
- [QUICKSTART.md](QUICKSTART.md): 빠른 시작 가이드
- [k8s/GPU_DEPLOYMENT_GUIDE.md](k8s/GPU_DEPLOYMENT_GUIDE.md): GPU 배포 가이드
- [monitoring/PROMETHEUS_GUIDE.md](monitoring/PROMETHEUS_GUIDE.md): 모니터링 가이드
- [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml): CI/CD 파이프라인
