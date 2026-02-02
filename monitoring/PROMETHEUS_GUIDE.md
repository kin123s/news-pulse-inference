# Kubernetes에서 Prometheus 모니터링 설정 가이드

## 1. Prometheus 설치 및 설정

### 기본 설치
```bash
# Prometheus를 K8s에 배포
kubectl apply -f k8s/prometheus-deployment.yaml

# Prometheus 서비스 확인
kubectl get svc -n news-analysis prometheus

# Prometheus UI 접속 (포트 포워딩)
kubectl port-forward -n news-analysis svc/prometheus 9090:9090
# 브라우저에서 http://localhost:9090 접속
```

## 2. 주요 메트릭

### Producer 메트릭
- `news_fetched_total`: 총 수집된 뉴스 수
- `news_sent_total`: Kafka로 전송된 뉴스 수
- `news_fetch_duration_seconds`: 뉴스 수집 소요 시간

### Consumer 메트릭
- `news_consumed_total`: Kafka에서 수신한 뉴스 수
- `news_analyzed_total`: 분석 완료된 뉴스 수
- `news_stored_total`: Redis에 저장된 뉴스 수
- `news_analysis_duration_seconds`: 분석 소요 시간
- `active_websocket_connections`: 활성 WebSocket 연결 수

## 3. 유용한 PromQL 쿼리

### 뉴스 처리율 (분당)
```promql
rate(news_consumed_total[1m])
```

### 평균 분석 시간
```promql
rate(news_analysis_duration_seconds_sum[5m]) / rate(news_analysis_duration_seconds_count[5m])
```

### WebSocket 연결 수
```promql
active_websocket_connections
```

### CPU 사용률 (Pod별)
```promql
rate(container_cpu_usage_seconds_total{namespace="news-analysis"}[5m])
```

### 메모리 사용량 (Pod별)
```promql
container_memory_usage_bytes{namespace="news-analysis"} / 1024 / 1024
```

## 4. HPA 테스트

### CPU 부하 생성 (테스트용)
```bash
# Producer에 부하 생성
kubectl run -n news-analysis load-generator --image=busybox --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://news-producer:8001/fetch-now; done"

# HPA 상태 확인
kubectl get hpa -n news-analysis

# Pod 스케일링 확인
kubectl get pods -n news-analysis -w
```

### 수동 스케일링 테스트
```bash
# 수동으로 replica 수 변경
kubectl scale deployment news-consumer --replicas=5 -n news-analysis

# 다시 HPA에 맡기기
kubectl scale deployment news-consumer --replicas=3 -n news-analysis
```

## 5. Grafana 대시보드 설정 (선택사항)

### Grafana 접속
```bash
# docker-compose 사용 시
# http://localhost:3000
# ID: admin, PW: admin

# K8s 환경에서는 별도 설치 필요
```

### 대시보드 구성 예시

1. **News Processing Dashboard**
   - 패널: 뉴스 수집/분석/저장 카운터
   - 패널: 처리 속도 그래프
   - 패널: 평균 처리 시간

2. **System Health Dashboard**
   - 패널: CPU/메모리 사용률
   - 패널: Pod 개수
   - 패널: WebSocket 연결 수

3. **HPA Dashboard**
   - 패널: Replica 수 변화
   - 패널: CPU/메모리 메트릭
   - 패널: 스케일링 이벤트

## 6. 알림 설정 (AlertManager)

### 예시 알림 규칙
```yaml
groups:
- name: news_analysis_alerts
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: rate(news_consumed_total[5m]) - rate(news_stored_total[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "높은 에러율 감지"
      
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes{namespace="news-analysis"} / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "메모리 사용률 90% 초과"
```

## 7. 로그 수집 (선택사항)

### Fluent Bit 또는 Fluentd 사용
```bash
# Fluent Bit DaemonSet 배포
kubectl apply -f https://raw.githubusercontent.com/fluent/fluent-bit-kubernetes-logging/master/fluent-bit-daemonset.yaml

# 로그를 Elasticsearch나 CloudWatch로 전송 가능
```

## 8. 트러블슈팅

### Prometheus가 메트릭을 수집하지 못할 때
```bash
# Prometheus 로그 확인
kubectl logs -n news-analysis -l app=prometheus

# 서비스 엔드포인트 확인
kubectl get endpoints -n news-analysis

# Pod annotation 확인
kubectl describe pod -n news-analysis -l app=news-consumer
```

### HPA가 작동하지 않을 때
```bash
# Metrics Server 설치 확인
kubectl get deployment metrics-server -n kube-system

# Metrics Server 설치 (없는 경우)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# HPA 상태 확인
kubectl describe hpa news-consumer-hpa -n news-analysis
```

## 9. 성능 최적화 팁

1. **Prometheus 데이터 보관 기간 설정**
   ```bash
   --storage.tsdb.retention.time=15d
   ```

2. **메트릭 수집 주기 조정**
   - 실시간성이 중요하면: `scrape_interval: 10s`
   - 비용 절감이 중요하면: `scrape_interval: 30s`

3. **HPA 반응 속도 조정**
   - `stabilizationWindowSeconds`: 스케일 다운 안정화 시간
   - `periodSeconds`: 메트릭 확인 주기

4. **리소스 제한 튜닝**
   - 초기에는 여유있게 설정
   - 실제 사용량 모니터링 후 조정
