---
description: 로컬 개발 환경 실행 워크플로우 (Docker Compose)
---

# 🚀 로컬 개발 환경 실행 (news-pulse-inference)

## 1. 사전 준비 (Prerequisites)

- [ ] Docker & Docker Compose 설치 확인
- [ ] Python 3.11+ (로컬 개발 모드 사용 시)
- [ ] News API 키 발급 (https://newsapi.org)
- [ ] `.env` 파일 설정 (NEWS_API_KEY 포함)

## 2. 전체 시스템 실행

```bash
# Docker Compose로 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

**접속 URL:**
- Inference API: http://localhost:8000
- Producer API: http://localhost:8001
- Consumer API: http://localhost:8002
- Frontend: http://localhost:80
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## 3. 로컬 개발 모드

```bash
# Python 의존성 설치
pip install -r requirements.txt

# Frontend 개발 서버
cd frontend && npm install && npm run dev
```

## 4. 테스트

```bash
# pytest 실행
python -m pytest tests/ -v

# 성능 테스트 포함
python -m pytest tests/test_inference.py -v -s
```

## 5. 에이전트 지침 (Agent Instructions)

- 본 워크플로우를 대리로 수행할 때는 각 단계별 성공/실패 여부를 코멘트로 남겨줄 것.
- Kafka/Redis 연결 실패 시 컨테이너 상태부터 확인할 것.
