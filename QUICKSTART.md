# 🚀 빠른 시작 가이드

새로운 개발자를 위한 1분 환경 구성 가이드

## ⚡ 1분 만에 시작하기

### 전제 조건
- Docker Desktop 설치
- Git 설치
- (선택사항) News API 키

### 단계별 실행

```bash
# 1. 저장소 클론
git clone <repository-url>
cd prj-py

# 2. 환경 변수 설정 (선택사항)
cp .env.example .env
# .env 파일을 열어 NEWS_API_KEY 설정 (선택사항)

# 3. 전체 스택 실행 (한 줄!)
docker-compose up -d

# 4. 상태 확인
docker-compose ps
```

**끝!** 이제 서비스가 준비되었습니다.

---

## 📍 서비스 접속

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Inference API** | http://localhost:8000 | 고성능 추론 서버 |
| **Producer API** | http://localhost:8001 | 뉴스 데이터 수집 |
| **Consumer API** | http://localhost:8002 | 실시간 분석 결과 |
| **Frontend** | http://localhost:80 | 실시간 대시보드 |
| **Prometheus** | http://localhost:9090 | 메트릭 모니터링 |
| **Grafana** | http://localhost:3000 | 데이터 시각화 |

```bash
# 전체 재시작
docker-compose restart

# 로그 보기
docker-compose logs -f producer
docker-compose logs -f consumer

# 특정 서비스만 재빌드
docker-compose up -d --build producer

# 전체 중지 및 삭제
docker-compose down

# 볼륨까지 삭제
docker-compose down -v
```

## 📊 데이터 확인

```bash
# Redis에 저장된 뉴스 확인
docker exec -it redis redis-cli
> KEYS news:*
> GET news:analysis:{news_id}

# Kafka 토픽 확인
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic news_stream \
  --from-beginning
```

## 🐛 문제 해결

### "Kafka is not available" 에러
- 해결: Kafka가 완전히 시작될 때까지 1-2분 대기

### "Redis connection refused" 에러
- 해결: `docker-compose restart redis`

### Frontend에서 데이터가 안 보임
- Backend가 실행 중인지 확인: `docker-compose ps`
- WebSocket 연결 확인: 브라우저 개발자 도구 Network 탭

## 📚 더 자세한 내용

- [전체 README](README.md)
- [Prometheus 모니터링 가이드](monitoring/PROMETHEUS_GUIDE.md)
- [Kubernetes 배포 가이드](k8s/README.md)
