# Phase D.1 Production Deployment Guide

## Overview

Phase D.1 (Production Deployment & Operations) provides complete Kubernetes deployment configuration, high availability setup, database replication, disaster recovery, infrastructure as code, secrets management, monitoring, logging, performance tuning, and security hardening for AgenticQuote.

## Prerequisites

- Kubernetes cluster (v1.28+)
- kubectl configured
- Terraform installed
- AWS account (if using AWS)
- Domain name configured

## Deployment Steps

### 1. Infrastructure Setup (Terraform)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This will create:
- VPC with private/public subnets
- EKS cluster with managed node groups
- Security groups
- IAM roles
- AWS Secrets Manager secrets

### 2. Kubernetes Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 3. Secrets Configuration

Create secrets from template:

```bash
cp k8s/secrets.template.yaml k8s/secrets.yaml
# Edit k8s/secrets.yaml with actual values
kubectl apply -f k8s/secrets.yaml
```

### 4. PostgreSQL Database

Deploy primary and replica:

```bash
kubectl apply -f k8s/postgres-primary.yaml
kubectl apply -f k8s/postgres-replica.yaml
kubectl apply -f k8s/postgres-services.yaml
```

### 5. Application Deployment

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
```

### 6. Load Balancing and Ingress

```bash
kubectl apply -f k8s/loadbalancer.yaml
kubectl apply -f k8s/ingress.yaml
```

### 7. Monitoring Stack

```bash
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana.yaml
kubectl apply -f k8s/grafana-datasources.yaml
kubectl apply -f k8s/grafana-dashboards.yaml
kubectl apply -f k8s/alertmanager.yaml
kubectl apply -f k8s/alertmanager-deployment.yaml
```

### 8. Logging Stack

```bash
kubectl apply -f k8s/elasticsearch.yaml
kubectl apply -f k8s/kibana.yaml
kubectl apply -f k8s/fluentd.yaml
```

### 9. Security Hardening

```bash
kubectl apply -f k8s/network-policies.yaml
kubectl apply -f k8s/security-contexts.yaml
kubectl apply -f k8s/cert-manager.yaml
```

### 10. Performance Tuning

```bash
kubectl apply -f k8s/resource-quotas.yaml
```

### 11. Backup Configuration

```bash
kubectl apply -f k8s/backup.yaml
```

## Verification

### Check Application Status

```bash
kubectl get pods -n production
kubectl get svc -n production
kubectl get ingress -n production
```

### Check Database Replication

```bash
kubectl exec -it postgres-primary-0 -n production -- psql -U postgres -d agenticquote -c "SELECT * FROM pg_stat_replication;"
```

### Check Monitoring

Access Grafana at `http://grafana.production.svc.cluster.local:3000`

### Check Logs

Access Kibana at `http://kibana.production.svc.cluster.local:5601`

## Rollback

```bash
kubectl rollout undo deployment/agenticquote -n production
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment agenticquote --replicas=5 -n production
```

### Auto Scaling is configured via HPA

## Troubleshooting

### Check Pod Logs

```bash
kubectl logs -f deployment/agenticquote -n production
```

### Check Events

```bash
kubectl get events -n production --sort-by='.lastTimestamp'
```

### Check Resource Usage

```bash
kubectl top pods -n production
kubectl top nodes
```

## Backup and Restore

### Manual Backup

```bash
kubectl exec -it postgres-primary-0 -n production -- pg_dump -U postgres agenticquote > backup.sql
```

### Restore

```bash
kubectl exec -i postgres-primary-0 -n production -- psql -U postgres agenticquote < backup.sql
```

## Security Notes

- All secrets are stored in AWS Secrets Manager
- Network policies restrict traffic
- Pod security policies enforce security contexts
- TLS certificates managed by cert-manager
- RBAC configured for least privilege

## Monitoring Alerts

Alerts are configured for:
- High error rates (> 5%)
- High latency (p95 > 2s)
- Pod crashes
- Database connection issues
- Low disk space

## Next Steps

Phase D.1 is complete. Next phases:
- Phase D.2: Real-Time Monitoring & Alerting
- Phase D.3: Advanced UI/UX
- Phase D.4: Mobile Application
- Phase D.5: API Gateway & Integrations
- Phase D.6: Advanced ML/AI
- Phase D.7: Advanced Reporting
