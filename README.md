# 📰 실시간 뉴스 분석 인퍼런스 서버

FastAPI, Kafka, Redis를 사용한 실시간 뉴스 데이터 스트리밍 및 분석 시스템

## 🎯 프로젝트 개요

이 프로젝트는 외부 뉴스 API에서 데이터를 수집하여 Kafka를 통해 스트리밍하고, 실시간으로 감성 분석 및 키워드 추출을 수행한 후, 결과를 Redis에 저장하고 Vue.js 프론트엔드에서 WebSocket을 통해 실시간으로 표시하는 시스템입니다.

## 🏗️ 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  News API   │────▶│  Producer   │────▶│    Kafka    │────▶│  Consumer   │
│  (External) │     │  (FastAPI)  │     │  (Stream)   │     │  (FastAPI)  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                                                                     ▼
                    ┌─────────────┐                         ┌─────────────┐
                    │  Frontend   │◀────────────────────────│    Redis    │
                    │   (Vue.js)  │      WebSocket          │  (Storage)  │
                    └─────────────┘                         └─────────────┘
```

## 🚀 주요 기능

- **실시간 뉴스 수집**: 외부 News API에서 자동으로 뉴스 수집
- **Kafka 스트리밍**: 고성능 데이터 파이프라인
- **AI 분석**: 감성 분석, 키워드 추출, 중요도 점수 계산
- **Redis 저장**: 빠른 데이터 조회 및 캐싱
- **WebSocket 실시간 피드**: 분석된 뉴스의 실시간 업데이트
- **HPA 자동 스케일링**: Kubernetes에서 부하에 따른 자동 확장
- **Prometheus 모니터링**: 메트릭 수집 및 시각화

## 📦 기술 스택

### Backend
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Kafka**: 실시간 데이터 스트리밍
- **Redis**: 인메모리 데이터 저장소
- **Python 3.11**: 최신 Python 기능 활용

### Frontend
- **Vue.js 3**: Composition API 사용
- **Vite**: 빠른 개발 환경
- **WebSocket**: 실시간 양방향 통신

### Infrastructure
- **Docker**: 컨테이너화
- **Kubernetes**: 오케스트레이션
- **Prometheus**: 모니터링
- **Grafana**: 시각화 (선택사항)

## 📋 사전 요구사항

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Kubernetes (Minikube, K3s, 또는 클라우드)
- News API 키 ([NewsAPI.org](https://newsapi.org)에서 무료 발급)

## 🛠️ 설치 및 실행

### 1. 로컬 개발 환경 (Docker Compose)

```bash
# 저장소 클론
git clone <repository-url>
cd prj-py

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 NEWS_API_KEY를 설정하세요

# Docker Compose로 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

**서비스 접속:**
- Producer API: http://localhost:8001
- Consumer API: http://localhost:8002
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Redis: localhost:6379
- Kafka: localhost:9092

### 2. Kubernetes 배포

```bash
# Docker 이미지 빌드
docker build -t news-producer:latest -f Dockerfile.producer .
docker build -t news-consumer:latest -f Dockerfile.consumer .

# Namespace 생성
kubectl apply -f k8s/namespace.yaml

# Secret 설정 (NEWS_API_KEY 변경 필요)
kubectl apply -f k8s/secret.yaml

# ConfigMap 적용
kubectl apply -f k8s/configmap.yaml

# Infrastructure 배포
kubectl apply -f k8s/kafka-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 서비스 배포
kubectl apply -f k8s/producer-deployment.yaml
kubectl apply -f k8s/consumer-deployment.yaml

# HPA 설정
kubectl apply -f k8s/hpa.yaml

# Prometheus 배포
kubectl apply -f k8s/prometheus-deployment.yaml

# 배포 상태 확인
kubectl get pods -n news-analysis
kubectl get svc -n news-analysis
kubectl get hpa -n news-analysis
```

### 3. Frontend 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드 (프로덕션)
npm run build
```

Frontend 접속: http://localhost:5173

## 📊 사용 방법

### API 엔드포인트

#### Producer Service (Port 8001)
```bash
# Health Check
curl http://localhost:8001/

# 수동 뉴스 수집 트리거
curl -X POST http://localhost:8001/fetch-now

# Prometheus 메트릭
curl http://localhost:8001/metrics
```

#### Consumer Service (Port 8002)
```bash
# Health Check
curl http://localhost:8002/

# 최근 뉴스 조회
curl http://localhost:8002/news/recent?limit=20

# 중요 뉴스 조회
curl http://localhost:8002/news/top?limit=10

# 특정 뉴스 조회
curl http://localhost:8002/news/{news_id}

# WebSocket 연결
wscat -c ws://localhost:8002/ws

# Prometheus 메트릭
curl http://localhost:8002/metrics
```

### WebSocket 메시지 형식

```javascript
// 초기 데이터
{
  "type": "initial_data",
  "data": [...] // 최근 뉴스 배열
}

// 새로운 분석 결과
{
  "type": "new_analysis",
  "data": {
    "id": "...",
    "title": "...",
    "description": "...",
    "analysis": {
      "sentiment": "positive|neutral|negative",
      "sentiment_score": 1.0,
      "keywords": ["keyword1", "keyword2"],
      "importance_score": 7.5
    }
  }
}
```

## 🔍 모니터링

### Prometheus 메트릭

**Producer 메트릭:**
- `news_fetched_total`: 총 수집된 뉴스 수
- `news_sent_total`: Kafka로 전송된 뉴스 수
- `news_fetch_duration_seconds`: 뉴스 수집 소요 시간

**Consumer 메트릭:**
- `news_consumed_total`: Kafka에서 수신한 뉴스 수
- `news_analyzed_total`: 분석 완료된 뉴스 수
- `news_stored_total`: Redis에 저장된 뉴스 수
- `news_analysis_duration_seconds`: 분석 소요 시간
- `active_websocket_connections`: 활성 WebSocket 연결 수

자세한 모니터링 가이드는 [monitoring/PROMETHEUS_GUIDE.md](monitoring/PROMETHEUS_GUIDE.md)를 참조하세요.

## 🧪 HPA 테스트

```bash
# CPU 부하 생성
kubectl run -n news-analysis load-generator \
  --image=busybox --restart=Never \
  -- /bin/sh -c "while true; do wget -q -O- http://news-producer:8001/fetch-now; done"

# HPA 상태 실시간 모니터링
kubectl get hpa -n news-analysis -w

# Pod 스케일링 확인
kubectl get pods -n news-analysis -w

# 부하 생성기 제거
kubectl delete pod load-generator -n news-analysis
```

## 🔧 커스터마이징

### 뉴스 소스 변경

[producer/news_client.py](producer/news_client.py)에서 다른 뉴스 API를 사용하도록 수정할 수 있습니다.

### 분석 로직 개선

[consumer/analyzer.py](consumer/analyzer.py)에서 더 정교한 ML 모델을 적용할 수 있습니다:
- Transformers (BERT, GPT)
- Named Entity Recognition (NER)
- Topic Modeling
- 딥러닝 감성 분석

### Kafka 파티션 증가

```bash
# Kafka에 접속하여 토픽 파티션 수 변경
docker exec -it kafka kafka-topics --alter \
  --zookeeper zookeeper:2181 \
  --topic news_stream \
  --partitions 6
```

## 📁 프로젝트 구조

```
prj-py/
├── producer/                 # Producer 서비스
│   ├── main.py              # FastAPI 앱
│   ├── kafka_producer.py    # Kafka 프로듀서
│   ├── news_client.py       # 뉴스 API 클라이언트
│   └── config.py            # 설정
├── consumer/                 # Consumer 서비스
│   ├── main.py              # FastAPI 앱
│   ├── kafka_consumer.py    # Kafka 컨슈머
│   ├── analyzer.py          # 뉴스 분석 로직
│   ├── redis_storage.py     # Redis 저장소
│   └── config.py            # 설정
├── frontend/                 # Vue.js 프론트엔드
│   ├── src/
│   │   ├── App.vue          # 메인 컴포넌트
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── k8s/                      # Kubernetes 매니페스트
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── producer-deployment.yaml
│   ├── consumer-deployment.yaml
│   ├── hpa.yaml
│   └── prometheus-deployment.yaml
├── monitoring/               # 모니터링 설정
│   ├── prometheus.yml
│   └── PROMETHEUS_GUIDE.md
├── docker-compose.yml        # Docker Compose 설정
├── Dockerfile.producer       # Producer Dockerfile
├── Dockerfile.consumer       # Consumer Dockerfile
├── requirements.txt          # Python 의존성
└── README.md                 # 이 파일
```

## 🐛 트러블슈팅

### Kafka 연결 오류
```bash
# Kafka가 시작될 때까지 대기
docker-compose logs kafka

# Kafka 토픽 확인
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Redis 연결 오류
```bash
# Redis 연결 테스트
docker exec -it redis redis-cli ping

# Redis 데이터 확인
docker exec -it redis redis-cli keys "*"
```

### WebSocket 연결 실패
- CORS 설정 확인
- 방화벽 설정 확인
- Consumer 서비스가 실행 중인지 확인

### HPA가 작동하지 않을 때
```bash
# Metrics Server 설치 확인
kubectl get deployment metrics-server -n kube-system

# 없으면 설치
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## 📚 학습 포인트

이 프로젝트를 통해 다음을 학습할 수 있습니다:

1. **비동기 프로그래밍**: FastAPI의 async/await 패턴
2. **메시지 큐**: Kafka를 통한 이벤트 드리븐 아키텍처
3. **마이크로서비스**: Producer/Consumer 분리 설계
4. **실시간 통신**: WebSocket 구현
5. **컨테이너화**: Docker 멀티 스테이지 빌드
6. **오케스트레이션**: Kubernetes 배포 및 관리
7. **자동 스케일링**: HPA를 통한 탄력적 확장
8. **모니터링**: Prometheus 메트릭 수집

## 🚀 다음 단계

프로젝트를 더 발전시키기 위한 아이디어:

- [ ] ML 모델 통합 (Transformers, BERT)
- [ ] 다국어 지원
- [ ] 뉴스 카테고리별 분류
- [ ] 사용자 인증 및 개인화
- [ ] Elasticsearch 통합 (전문 검색)
- [ ] CI/CD 파이프라인 구축
- [ ] 부하 테스트 (Locust, K6)
- [ ] A/B 테스트 기능
- [ ] 알림 시스템 (이메일, Slack)
- [ ] 데이터 시각화 대시보드 개선

## 📄 라이센스

MIT License

## 👥 기여

이슈와 PR을 환영합니다!

## 📧 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**Happy Coding! 🎉**
