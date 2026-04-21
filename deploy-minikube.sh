#!/bin/bash
# HMS Minikube Deployment Script
# Usage: ./deploy-minikube.sh [--build] [--load] [--setup] [--deploy] [--up] [--status] [--delete]

set -e

NAMESPACE="hospital-system"
PROJECT_DIR="/home/prakash/Assignment_ScalableServices/repos"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v minikube &> /dev/null; then
        log_error "minikube not found"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "docker not found"
        exit 1
    fi
    
    if ! minikube status &> /dev/null; then
        log_warn "Minikube not running. Starting..."
        minikube start
    fi
    
    log_success "Prerequisites OK"
    minikube status | grep -E "host:|kubelet:|apiserver:"
}

# Build Docker images in minikube (tag for K8s deployment)
build_images() {
    log_info "Building Docker images in Minikube..."
    
    # Use minikube's internal Docker daemon
    eval $(minikube docker-env)
    
    SERVICES=(
        "patient-service"
        "doctor-service"
        "appointment-service"
        "billing-service"
        "prescription-service"
        "payment-service"
        "notification-service"
    )
    
    for svc in "${SERVICES[@]}"; do
        echo -n "Building $svc... "
        # Build and tag with :latest
        docker build -t "$svc:latest" "$PROJECT_DIR/$svc" 2>&1 | tail -1
        log_success "$svc:latest"
    done
    
    # Exit minikube docker env
    eval $(minikube docker-env -u) 2>/dev/null || true
    
    log_success "All images built and tagged in minikube"
    
    # List available images
    echo ""
    echo "Available images in minikube:"
    eval $(minikube docker-env)
    docker images | grep service
    eval $(minikube docker-env -u) 2>/dev/null || true
}

# Setup namespace and storage
setup_storage() {
    log_info "Setting up Kubernetes storage..."
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl apply -f "$PROJECT_DIR/k8s/pvc.yaml" -n "$NAMESPACE"
    
    log_success "Storage configured"
}

# Deploy to Kubernetes
deploy() {
    log_info "Deploying to Kubernetes..."
    
    kubectl apply -f "$PROJECT_DIR/k8s/deployment.yaml" -n "$NAMESPACE"
    
    log_success "Deployment complete"
}

# Wait for pods
wait_pods() {
    log_info "Waiting for pods (max 60s)..."
    for i in {1..12}; do
        READY=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -o True | wc -l)
        TOTAL=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
        
        if [ "$READY" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
            log_success "All pods ready"
            return 0
        fi
        
        echo "  Waiting... ($READY/$TOTAL ready)"
        sleep 5
    done
    
    log_warn "Some pods may not be ready yet"
}

# Show status
status() {
    echo ""
    echo "=========================================="
    echo -e "       ${CYAN}HMS MINIKUBE STATUS${NC}"
    echo "=========================================="
    echo ""
    
    echo "=== Minikube ==="
    minikube status | grep -E "^(host|kubelet|apiserver):"
    
    echo ""
    echo "=== K8s Resources ==="
    kubectl get all,ingress -n "$NAMESPACE" --no-headers 2>/dev/null
    
    echo ""
    echo "=== Pods ==="
    kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null
    
    echo ""
    echo "=== Services ==="
    kubectl get svc -n "$NAMESPACE" --no-headers 2>/dev/null
}

# Delete
delete() {
    log_info "Deleting HMS from Kubernetes..."
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
    log_success "HMS deleted"
}

# Help
show_help() {
    echo "HMS Minikube Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  --build     Build Docker images in minikube"
    echo "  --setup     Create namespace and PVCs"
    echo "  --deploy    Deploy to Kubernetes"
    echo "  --up        Full deployment (build + setup + deploy)"
    echo "  --status    Show deployment status"
    echo "  --delete    Delete deployment"
    echo "  --help      Show this help"
    echo ""
    echo "Important Notes:"
    echo "  - K8s pods in minikube may have image pull issues"
    echo "  - For local development, use: docker-compose up -d"
    echo "  - This script is ready for production K8s clusters"
    echo ""
    echo "Examples:"
    echo "  $0 --build     # Build images"
    echo "  $0 --up        # Full deployment"
    echo "  $0 --status    # Check status"
}

# Main
case "${1:-}" in
    --build)
        check_prerequisites && build_images
        ;;
    --setup)
        check_prerequisites && setup_storage
        ;;
    --deploy)
        check_prerequisites && deploy && wait_pods
        ;;
    --up)
        check_prerequisites && build_images && setup_storage && deploy && wait_pods && status
        ;;
    --status)
        status
        ;;
    --delete)
        delete
        ;;
    --help|-h|"")
        show_help
        ;;
    *)
        log_error "Unknown: $1"
        show_help
        exit 1
        ;;
esac