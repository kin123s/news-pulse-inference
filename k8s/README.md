# Kubernetes 배포 가이드

## 전제 조건

- Kubernetes 클러스터 (Minikube, K3s, EKS, GKE 등)
- kubectl 설치 및 구성
- Docker 이미지 레지스트리 (Docker Hub, ECR, GCR 등)

## 1. Docker 이미지 빌드 및 푸시

### 로컬 빌드 (Minikube 사용 시)
```bash
# Minikube의 Docker 환경 사용
eval $(minikube docker-env)

# 이미지 빌드
docker build -t news-producer:latest -f Dockerfile.producer .
docker build -t news-consumer:latest -f Dockerfile.consumer .
```

### Docker Hub로 푸시
```bash
# 이미지 태그
docker tag news-producer:latest yourusername/news-producer:latest
docker tag news-consumer:latest yourusername/news-consumer:latest

# 푸시
docker push yourusername/news-producer:latest
docker push yourusername/news-consumer:latest

# Deployment 파일에서 이미지 경로 수정
# image: news-producer:latest → image: yourusername/news-producer:latest
```

## 2. Namespace 생성

```bash
kubectl apply -f k8s/namespace.yaml
```

## 3. Secret 설정

```bash
# Secret 파일 편집 (News API 키 입력)
vi k8s/secret.yaml

# 적용
kubectl apply -f k8s/secret.yaml

# 확인
kubectl get secret -n news-analysis
```

## 4. ConfigMap 적용

```bash
kubectl apply -f k8s/configmap.yaml
kubectl get configmap -n news-analysis
```

## 5. Infrastructure 배포

### Kafka 배포
```bash
kubectl apply -f k8s/kafka-deployment.yaml

# 확인
kubectl get pods -n news-analysis -l app=kafka
kubectl logs -n news-analysis -l app=kafka -c kafka
```

### Redis 배포
```bash
kubectl apply -f k8s/redis-deployment.yaml

# 확인
kubectl get pods -n news-analysis -l app=redis
```

## 6. Application 배포

### Producer 배포
```bash
kubectl apply -f k8s/producer-deployment.yaml

# 확인
kubectl get pods -n news-analysis -l app=news-producer
kubectl logs -n news-analysis -l app=news-producer
```

### Consumer 배포
```bash
kubectl apply -f k8s/consumer-deployment.yaml

# 확인
kubectl get pods -n news-analysis -l app=news-consumer
kubectl logs -n news-analysis -l app=news-consumer
```

## 7. HPA 설정

### Metrics Server 설치 (필요한 경우)
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Minikube에서는 추가 설정 필요
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

### HPA 적용
```bash
kubectl apply -f k8s/hpa.yaml

# 확인
kubectl get hpa -n news-analysis
kubectl describe hpa news-producer-hpa -n news-analysis
kubectl describe hpa news-consumer-hpa -n news-analysis
```

## 8. Prometheus 배포

```bash
kubectl apply -f k8s/prometheus-deployment.yaml

# 확인
kubectl get pods -n news-analysis -l app=prometheus
kubectl get svc -n news-analysis prometheus
```

## 9. 서비스 접속

### 포트 포워딩 (개발 환경)
```bash
# Producer
kubectl port-forward -n news-analysis svc/news-producer 8001:8001

# Consumer
kubectl port-forward -n news-analysis svc/news-consumer 8002:8002

# Prometheus
kubectl port-forward -n news-analysis svc/prometheus 9090:9090
```

### LoadBalancer (프로덕션 환경)
```bash
# External IP 확인
kubectl get svc -n news-analysis

# Minikube에서 LoadBalancer 활성화
minikube tunnel
```

## 10. 배포 확인

```bash
# 전체 리소스 확인
kubectl get all -n news-analysis

# Pod 상태 확인
kubectl get pods -n news-analysis -o wide

# 로그 확인
kubectl logs -n news-analysis -l app=news-consumer --tail=100

# 이벤트 확인
kubectl get events -n news-analysis --sort-by='.lastTimestamp'
```

## 11. HPA 테스트

```bash
# 부하 생성기 실행
kubectl run -n news-analysis load-generator \
  --image=busybox --restart=Never \
  -- /bin/sh -c "while true; do wget -q -O- http://news-producer:8001/fetch-now; sleep 0.5; done"

# HPA 상태 모니터링 (별도 터미널)
watch kubectl get hpa -n news-analysis

# Pod 스케일링 모니터링 (별도 터미널)
watch kubectl get pods -n news-analysis

# 부하 생성기 제거
kubectl delete pod load-generator -n news-analysis
```

## 12. 스케일링 조정

### 수동 스케일링
```bash
# Producer 스케일 업
kubectl scale deployment news-producer --replicas=5 -n news-analysis

# Consumer 스케일 다운
kubectl scale deployment news-consumer --replicas=2 -n news-analysis
```

### HPA 파라미터 수정
```yaml
# k8s/hpa.yaml 편집
spec:
  minReplicas: 2      # 최소 Pod 수
  maxReplicas: 20     # 최대 Pod 수
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # CPU 목표 사용률
```

## 13. 업데이트 및 롤백

### Rolling Update
```bash
# 새 이미지로 업데이트
kubectl set image deployment/news-consumer \
  consumer=yourusername/news-consumer:v2 \
  -n news-analysis

# 업데이트 상태 확인
kubectl rollout status deployment/news-consumer -n news-analysis
```

### 롤백
```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/news-consumer -n news-analysis

# 특정 리비전으로 롤백
kubectl rollout undo deployment/news-consumer --to-revision=2 -n news-analysis

# 롤아웃 히스토리 확인
kubectl rollout history deployment/news-consumer -n news-analysis
```

## 14. 정리

```bash
# 전체 삭제
kubectl delete namespace news-analysis

# 또는 개별 삭제
kubectl delete -f k8s/
```

## 트러블슈팅

### Pod가 Pending 상태
```bash
kubectl describe pod <pod-name> -n news-analysis
# 리소스 부족, 볼륨 마운트 실패 등 확인
```

### ImagePullBackOff 에러
```bash
# 이미지 이름 확인
kubectl describe pod <pod-name> -n news-analysis

# imagePullPolicy 변경
# imagePullPolicy: IfNotPresent (로컬 이미지 우선 사용)
```

### CrashLoopBackOff 에러
```bash
# 로그 확인
kubectl logs <pod-name> -n news-analysis --previous

# 환경 변수 확인
kubectl exec -it <pod-name> -n news-analysis -- env
```

### HPA가 작동하지 않음
```bash
# Metrics Server 확인
kubectl top nodes
kubectl top pods -n news-analysis

# HPA 이벤트 확인
kubectl describe hpa <hpa-name> -n news-analysis
```

## 프로덕션 권장 사항

1. **Resource Limits 설정**: 모든 Pod에 적절한 리소스 제한 설정
2. **Liveness/Readiness Probes**: 헬스 체크 엔드포인트 구현
3. **PersistentVolume**: Redis, Kafka에 영구 스토리지 사용
4. **Ingress Controller**: 외부 트래픽 관리
5. **TLS/SSL**: 보안 통신 설정
6. **Network Policies**: Pod 간 통신 제한
7. **RBAC**: 최소 권한 원칙 적용
8. **Logging**: EFK 스택 또는 CloudWatch 사용
9. **Monitoring**: Prometheus + Grafana 대시보드 구성
10. **Backup**: 정기적인 백업 및 복구 계획

## 클라우드별 설정

### AWS EKS
```bash
# ALB Ingress Controller 설치
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# Service를 LoadBalancer로 노출
# annotations에 AWS 관련 설정 추가
```

### GCP GKE
```bash
# GKE Autopilot 사용 시 리소스 요청 필수
# Workload Identity 설정
```

### Azure AKS
```bash
# Application Gateway Ingress Controller 사용
# Azure Monitor 통합
```
