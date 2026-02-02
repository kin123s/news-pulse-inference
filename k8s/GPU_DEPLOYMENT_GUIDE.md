# K8s 배포 가이드 - GPU 리소스 고려

## 🚀 빠른 시작

### 1. Prerequisites

```bash
# Kubernetes 클러스터 (Minikube, K3s, GKE, EKS, AKS 등)
kubectl version

# Helm (선택사항)
helm version

# Metrics Server (HPA를 위해 필요)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 2. Namespace 생성

```bash
kubectl apply -f namespace.yaml
```

### 3. Secret 설정

```bash
# API 키 설정
kubectl create secret generic api-secrets \
  --from-literal=openai-api-key=YOUR_OPENAI_KEY \
  --from-literal=news-api-key=YOUR_NEWS_API_KEY \
  -n news-analysis

# 또는 YAML 파일 수정 후 적용
kubectl apply -f secret.yaml
```

### 4. 인프라 배포

```bash
# Kafka
kubectl apply -f kafka-deployment.yaml

# Redis
kubectl apply -f redis-deployment.yaml

# Prometheus (모니터링)
kubectl apply -f prometheus-deployment.yaml
```

### 5. 애플리케이션 배포

```bash
# Producer
kubectl apply -f producer-deployment.yaml

# Consumer
kubectl apply -f consumer-deployment.yaml

# Inference Server (NEW!)
kubectl apply -f inference-deployment.yaml
```

### 6. 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n news-analysis

# 서비스 확인
kubectl get svc -n news-analysis

# HPA 상태 확인
kubectl get hpa -n news-analysis

# 로그 확인
kubectl logs -f deployment/inference-server -n news-analysis
```

---

## 🎯 GPU 리소스 설정

### GPU 노드 설정 (GKE 예시)

```bash
# GPU 노드 풀 생성
gcloud container node-pools create gpu-pool \
  --cluster=news-analysis-cluster \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --machine-type=n1-standard-4 \
  --num-nodes=1 \
  --min-nodes=0 \
  --max-nodes=3 \
  --enable-autoscaling

# NVIDIA GPU Operator 설치
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/gpu-operator/master/deployments/gpu-operator.yaml
```

### GPU 리소스 요청 활성화

[inference-deployment.yaml](inference-deployment.yaml)에서 아래 부분 주석 해제:

```yaml
resources:
  requests:
    nvidia.com/gpu: "1"
  limits:
    nvidia.com/gpu: "1"

nodeSelector:
  accelerator: nvidia-tesla-t4

tolerations:
- key: nvidia.com/gpu
  operator: Exists
  effect: NoSchedule
```

### GPU 사용 확인

```bash
# GPU 리소스 확인
kubectl describe nodes | grep -A 5 "Allocated resources"

# GPU 사용 중인 Pod 확인
kubectl get pods -n news-analysis -o wide
```

---

## 📊 HPA (Horizontal Pod Autoscaling)

### Metrics Server 설치 확인

```bash
kubectl get deployment metrics-server -n kube-system
```

### HPA 설정

현재 HPA는 다음 메트릭을 기반으로 스케일링:

1. **CPU 사용률**: 70% 이상
2. **메모리 사용률**: 80% 이상
3. **커스텀 메트릭**: 초당 추론 요청 수

### 커스텀 메트릭 (Prometheus Adapter)

```bash
# Prometheus Adapter 설치
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace news-analysis \
  --set prometheus.url=http://prometheus:9090 \
  --set rules.default=false \
  --set-file rules.custom=prometheus-adapter-rules.yaml
```

### 부하 테스트

```bash
# kubectl run으로 부하 생성
kubectl run -it --rm load-generator \
  --image=busybox \
  --restart=Never \
  -n news-analysis \
  -- /bin/sh -c "while true; do wget -q -O- http://inference-server:8000/health; done"

# HPA 스케일링 확인
kubectl get hpa inference-server-hpa -n news-analysis --watch
```

---

## 🔍 모니터링 및 디버깅

### Prometheus 메트릭 확인

```bash
# Prometheus UI 접속
kubectl port-forward svc/prometheus -n news-analysis 9090:9090

# 브라우저에서 http://localhost:9090 접속
```

주요 메트릭:
- `inference_requests_total`: 총 추론 요청 수
- `inference_duration_seconds`: 추론 처리 시간
- `inference_batch_size`: 배치 크기
- `active_inference_tasks`: 실행 중인 추론 작업 수
- `kafka_consumer_lag`: Kafka 컨슈머 지연

### Grafana 대시보드 (선택사항)

```bash
# Grafana 설치
helm install grafana grafana/grafana -n news-analysis

# Admin 비밀번호 확인
kubectl get secret grafana -n news-analysis -o jsonpath="{.data.admin-password}" | base64 --decode

# Grafana 접속
kubectl port-forward svc/grafana -n news-analysis 3000:3000
```

### 로그 확인

```bash
# 특정 Pod 로그
kubectl logs -f <pod-name> -n news-analysis

# 모든 inference server 로그
kubectl logs -f deployment/inference-server -n news-analysis

# 에러만 필터링
kubectl logs deployment/inference-server -n news-analysis | grep ERROR
```

---

## 🔄 업데이트 및 롤백

### Rolling Update

```bash
# 이미지 업데이트
kubectl set image deployment/inference-server \
  inference=news-inference:v2.0 \
  -n news-analysis

# 롤아웃 상태 확인
kubectl rollout status deployment/inference-server -n news-analysis
```

### 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/inference-server -n news-analysis

# 특정 리비전으로 롤백
kubectl rollout undo deployment/inference-server --to-revision=2 -n news-analysis

# 롤아웃 히스토리
kubectl rollout history deployment/inference-server -n news-analysis
```

---

## 💾 리소스 최적화

### Vertical Pod Autoscaler (VPA)

```bash
# VPA 설치
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-0.14.0/vpa-v0.14.0.yaml

# VPA 설정
kubectl apply -f - <<EOF
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: inference-server-vpa
  namespace: news-analysis
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-server
  updatePolicy:
    updateMode: "Auto"
EOF
```

### Pod Disruption Budget

```bash
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: inference-server-pdb
  namespace: news-analysis
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: inference-server
EOF
```

---

## 🧪 성능 튜닝

### 대량 유입 시 스케일 아웃 설정

현재 HPA 설정:
- **최소 레플리카**: 2
- **최대 레플리카**: 20
- **스케일업**: 즉시 (안정화 0초)
- **스케일다운**: 5분 안정화

대량 트래픽 예상 시:

```bash
# 수동 스케일링
kubectl scale deployment inference-server --replicas=10 -n news-analysis

# HPA 최소값 증가
kubectl patch hpa inference-server-hpa -n news-analysis \
  --patch '{"spec":{"minReplicas":5}}'
```

### 리소스 제한 조정

고부하 환경:
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

저부하 환경:
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

---

## 🔒 보안 고려사항

### Network Policies

```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: inference-server-netpol
  namespace: news-analysis
spec:
  podSelector:
    matchLabels:
      app: inference-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: consumer
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: kafka
    ports:
    - protocol: TCP
      port: 9093
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
EOF
```

---

## 📚 추가 리소스

- [Kubernetes GPU 가이드](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [HPA 상세 문서](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Prometheus Adapter](https://github.com/kubernetes-sigs/prometheus-adapter)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/getting-started.html)
