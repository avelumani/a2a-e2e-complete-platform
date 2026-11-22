#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== 1. Creating kind cluster 'a2a-gitops' ==="
kind create cluster --name a2a-gitops --config "$SCRIPT_DIR/kind-cluster.yaml"

echo "=== 2. Installing cert-manager & ClickHouse Operator ==="
helm install cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.20.2 \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true

kubectl wait --for=condition=Established \
  crd/certificates.cert-manager.io crd/issuers.cert-manager.io --timeout=120s

helm install clickhouse-operator oci://ghcr.io/clickhouse/clickhouse-operator-helm \
  --version 0.0.8 \
  --namespace clickhouse-operator --create-namespace

kubectl wait --for=condition=Established \
  crd/clickhouseclusters.clickhouse.com crd/keeperclusters.clickhouse.com --timeout=120s

echo "=== 3. Installing Argo CD ==="
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd \
  --namespace argocd --create-namespace \
  --set server.service.type=NodePort \
  --set server.service.nodePortHttps=30443 \
  --set configs.params."server\.insecure"=true \
  --wait

echo "=== 4. Installing Kargo CD ==="
PASS_HASH=$(python3 -c 'import crypt; print(crypt.crypt("admin", crypt.mksalt(crypt.METHOD_BLOWFISH)))' 2>/dev/null || echo '$2y$10$8K1p/a0dL1LXMIgoEDFrwOfMQ16/1nK9.7P1S/m4T1xO8wR4dF9G.')
helm install kargo oci://ghcr.io/akuity/kargo-charts/kargo \
  --namespace kargo --create-namespace \
  --set api.service.type=NodePort \
  --set api.service.nodePort=30444 \
  --set api.adminAccount.passwordHash="$PASS_HASH" \
  --set api.adminAccount.tokenSigningKey="local-kargo-signing-secret-key-12345" \
  --set controller.argocd.integrationEnabled=true \
  --set controller.argocd.namespace=argocd \
  --wait

echo "=== 5. Installing Langfuse Observability ==="
kubectl create namespace langfuse --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic langfuse-secrets -n langfuse \
  --from-literal=salt="$(openssl rand -hex 32)" \
  --from-literal=encryptionKey="$(openssl rand -hex 32)" \
  --from-literal=nextauth-secret="$(openssl rand -hex 32)" \
  --from-literal=postgres-password="langfuse-pg-password" \
  --from-literal=clickhouse-password="langfuse-ch-password" \
  --from-literal=redis-password="langfuse-redis-password" \
  --from-literal=s3-access-key-id="langfuse-s3-user" \
  --from-literal=s3-secret-access-key="langfuse-s3-secret" \
  --dry-run=client -o yaml | kubectl apply -f -

helm install langfuse oci://ghcr.io/langfuse/langfuse-k8s/charts/langfuse \
  --version 2.0.0 \
  --namespace langfuse \
  -f "$SCRIPT_DIR/langfuse-values.yaml" \
  --wait

echo "=== 6. Building & Loading 4 A2A Agent Images into kind ==="
for svc in orchestrator triage allocation credit; do
  docker build -t "a2a-${svc}-agent:v0.1.0" "$ROOT_DIR/${svc}-agent-repo"
  kind load docker-image "a2a-${svc}-agent:v0.1.0" --name a2a-gitops
done

echo ""
echo "=================================================================="
echo "BOOTSTRAP COMPLETE!"
echo "Argo CD UI : https://localhost:8443  (user: admin)"
echo "Argo Pass  : $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
echo "Kargo UI   : http://localhost:8444   (user: admin / pass: admin)"
echo "Langfuse UI: http://localhost:3000"
echo "=================================================================="
