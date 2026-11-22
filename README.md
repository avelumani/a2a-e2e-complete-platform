# Complete End-to-End A2A Multi-Repo Order Management + kind + Argo CD + Kargo + Langfuse

Everything needed to run the 4 independent A2A microservices (`orchestrator`, `triage`, `allocation`, `credit`) locally on Ubuntu WSL inside a `kind` Kubernetes cluster with Argo CD, Kargo CD, and Langfuse observability.

## Directory Layout
- `orchestrator-agent-repo/` (Port 8000, Dockerfile, LangGraph + A2A + Langfuse)
- `triage-agent-repo/` (Port 8001, Dockerfile, LangGraph + A2A + Langfuse)
- `allocation-agent-repo/` (Port 8002, Dockerfile, LangGraph + A2A + Langfuse)
- `credit-agent-repo/` (Port 8003, Dockerfile, LangGraph + A2A + Langfuse)
- `platform-infra/` (`kind-cluster.yaml`, `langfuse-values.yaml`, and one-click `bootstrap_cluster.sh`)
- `gitops-repo/` (`order-agents-chart/`, `kargo-manifests/`, `argocd-manifests/`)
- `e2e_test_client.py` (End-to-end test script hitting `http://localhost:8000/a2a`)

## Quick Start
```bash
chmod +x platform-infra/bootstrap_cluster.sh
./platform-infra/bootstrap_cluster.sh
```
