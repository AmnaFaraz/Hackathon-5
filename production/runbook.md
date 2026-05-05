# Incident Response Runbook

This document outlines standard operating procedures for the Customer Success FTE system.

## On-Call Contacts
- **Primary**: Check Kubernetes pod logs first.
- **Escalation**: Human support team via Slack `#support-escalations`.

## Common Incidents

### Incident 1: API pods not responding
- **Symptoms**: `/health` returns 503.
- **Steps**:
    1. `kubectl get pods -n customer-success-fte`
    2. `kubectl logs {pod-name} -n customer-success-fte`
    3. `kubectl rollout restart deployment/fte-api -n customer-success-fte`

### Incident 2: Kafka consumer lag
- **Symptoms**: Messages processing slowly, tickets delayed.
- **Steps**:
    1. Check consumer group lag.
    2. Restart worker pods.
    3. `kubectl rollout restart deployment/fte-message-processor -n customer-success-fte`

### Incident 3: Gmail webhook failures
- **Symptoms**: Emails not being processed.
- **Steps**:
    1. Check `/webhooks/gmail` endpoint.
    2. Verify Pub/Sub subscription active.
    3. Re-run `setup_push_notifications()` in the gmail handler context.

### Incident 4: WhatsApp webhook 403 errors
- **Symptoms**: Twilio webhook failing signature validation.
- **Steps**:
    1. Verify `TWILIO_AUTH_TOKEN` in `secrets.yaml` matches Twilio console.
    2. Redeploy secrets: `kubectl apply -f production/k8s/secrets.yaml`.

### Incident 5: Database connection pool exhausted
- **Symptoms**: `asyncpg.TimeoutError` in logs.
- **Steps**:
    1. `kubectl describe pod`
    2. Check `POSTGRES_MAX_CONNECTIONS` env var.
    3. Restart API and worker deployments to clear stale connections.

## Daily Health Checks
- **GET /health** → expect `{"status": "healthy"}`
- **GET /metrics/channels** → verify all 3 channels showing data
- **Check Kubernetes HPA**: `kubectl get hpa -n customer-success-fte`

## 24-Hour Test Validation Checklist
- [ ] Uptime > 99.9%
- [ ] P95 latency < 3 seconds
- [ ] Escalation rate < 25%
- [ ] Cross-channel identification > 95%
- [ ] Zero message loss confirmed in Kafka DLQ
