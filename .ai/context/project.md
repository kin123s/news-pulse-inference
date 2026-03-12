---
description: 프로젝트 핵심 문맥 및 구조 요약 정보
---

# 🏢 프로젝트 컨텍스트 (Project Context)

> **안내:** 이 문서는 프로젝트의 전반적인 목적, 아키텍처, 주요 디렉토리 구조 등을 에이전트가 빠르게 파악할 수 있도록 작성하는 컨텍스트 문서입니다.

## 1. 프로젝트 개요

- **프로젝트명:** news-pulse-inference (고성능 비동기 스트림 처리 기반 뉴스 분석 엔진)
- **목표:** 대용량 데이터 파이프라인을 위한 고성능 비동기 추론 엔진. Faust-Streaming으로 Kafka 스트림 실시간 처리, asyncio.gather로 외부 AI API 병렬 호출, Pydantic V2로 타입 안전성 보장.
- **주요 기술 스택:**
  - Backend: Python 3.11+, FastAPI 0.109+, Faust-Streaming 0.10+
  - Frontend: Vue.js 3 (Composition API), Vite, WebSocket
  - Infrastructure: Docker, Docker Compose, Kubernetes (HPA)
  - Database/Cache: Redis (인메모리 저장소)
  - Message Broker: Apache Kafka + aiokafka (비동기 클라이언트)
  - AI/ML: OpenAI API (선택), HuggingFace (선택), 로컬 휴리스틱 분석
  - Monitoring: Prometheus 커스텀 메트릭, Grafana
  - Validation: Pydantic V2 (엄격한 데이터 검증 + 정규화)

## 2. 보안 및 규정 (Security & Compliance)

- **인증/인가 방식:** 현재 미구현 (WebSocket 인증 추가 예정)
- **데이터 처리 주의사항:** NEWS_API_KEY 관리 (K8s Secret 또는 .env), 외부 AI API 키 보호
- **보안 검토 사항:** Dockerfile multi-stage build 적용, Rate limiting (Semaphore)

## 3. 디렉토리 구조 (Directory Structure)

```text
/
├── .ai/                      # AI 에이전트 전역 규칙 및 컨텍스트
├── .github/workflows/        # CI/CD 파이프라인
├── producer/                 # Producer 서비스 (뉴스 수집)
│   ├── main.py               # FastAPI 앱
│   ├── kafka_producer.py     # Kafka 프로듀서
│   └── news_client.py        # 뉴스 API 클라이언트
├── consumer/                 # Consumer 서비스 (뉴스 처리 + 저장)
│   ├── main.py               # FastAPI 앱
│   ├── kafka_consumer.py     # Kafka 컨슈머
│   ├── analyzer.py           # 뉴스 분석 로직
│   └── redis_storage.py      # Redis 저장소
├── inference/                # 추론 엔진 (핵심)
│   ├── main.py               # FastAPI 추론 API
│   ├── async_inference_engine.py  # asyncio.gather 기반 병렬 추론
│   ├── stream_processor.py   # Faust-Streaming 프로세서
│   └── models.py             # Pydantic V2 모델
├── frontend/                 # Vue.js 3 대시보드
├── k8s/                      # Kubernetes 매니페스트
├── monitoring/               # Prometheus 설정
├── tests/                    # pytest 테스트
├── docker-compose.yml        # Docker Compose
├── Dockerfile.producer       # Producer Dockerfile
├── Dockerfile.consumer       # Consumer Dockerfile
├── Dockerfile.inference      # Inference Dockerfile
└── requirements.txt          # Python 의존성
```

## 4. 특이사항 및 히스토리 (Notes & History)

- **알려진 이슈:** 외부 AI API 호출이 `asyncio.sleep(0.1)` 시뮬레이션만 적용 — 실제 모델 통합 필요
- **테스트 현황:** pytest-asyncio 기반 통합 테스트 7개 (배치 처리, 감성 분석, 키워드 추출, 성능, 에러 핸들링)
- **감성 분석:** 현재 영어 키워드 18~19개 기반 휴리스틱 — BERT/Transformers 모델 통합 권장
- **.env.example 미제공:** 환경 변수 설정 가이드 명확화 필요
