# Fuellhorn Helm Chart

Self-hosted food inventory management for Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2+
- PV provisioner support (for SQLite persistence)

## Installation

### Quick Start (Testing)

```bash
helm install fuellhorn ./charts/fuellhorn \
  --set secrets.secretKey="your-secret-key-min-32-chars-here" \
  --set secrets.fuellhornSecret="your-fuellhorn-secret-min-32-chars"
```

### Production with PostgreSQL

```bash
helm install fuellhorn ./charts/fuellhorn \
  --set database.type=postgresql \
  --set database.external.host=postgres.example.com \
  --set database.external.password=mypassword \
  --set secrets.existingSecret=my-fuellhorn-secrets
```

### Using Existing Secrets

Create secrets beforehand:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-fuellhorn-secrets
type: Opaque
data:
  secret-key: <base64-encoded-secret-key>
  fuellhorn-secret: <base64-encoded-fuellhorn-secret>
```

Then install:

```bash
helm install fuellhorn ./charts/fuellhorn \
  --set secrets.existingSecret=my-fuellhorn-secrets
```

## Configuration

### General

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `ghcr.io/jensens/fuellhorn` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `imagePullSecrets` | Image pull secrets | `[]` |
| `nameOverride` | Override chart name | `""` |
| `fullnameOverride` | Override full name | `""` |

### Service

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8080` |

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `""` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.hosts` | Ingress hosts configuration | See values.yaml |
| `ingress.tls` | TLS configuration | `[]` |

### Database

| Parameter | Description | Default |
|-----------|-------------|---------|
| `database.type` | Database type (`postgresql` or `sqlite`) | `postgresql` |
| `database.external.host` | PostgreSQL host | `""` |
| `database.external.port` | PostgreSQL port | `5432` |
| `database.external.database` | Database name | `fuellhorn` |
| `database.external.username` | Database username | `fuellhorn` |
| `database.external.password` | Database password (not recommended for production) | `""` |
| `database.external.existingSecret` | Existing secret with password key | `""` |

### Secrets

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.existingSecret` | Name of existing secret | `""` |
| `secrets.secretKey` | Flask secret key (required if no existingSecret) | `""` |
| `secrets.fuellhornSecret` | Fuellhorn secret (required if no existingSecret) | `""` |

### Persistence (SQLite only)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistence | `true` |
| `persistence.storageClass` | Storage class | `""` |
| `persistence.size` | PVC size | `1Gi` |
| `persistence.accessMode` | PVC access mode | `ReadWriteOnce` |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Health Checks

| Parameter | Description | Default |
|-----------|-------------|---------|
| `livenessProbe` | Liveness probe configuration | See values.yaml |
| `readinessProbe` | Readiness probe configuration | See values.yaml |

## Examples

### SQLite with Ingress

```yaml
database:
  type: sqlite

persistence:
  enabled: true
  size: 5Gi

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: fuellhorn.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: fuellhorn-tls
      hosts:
        - fuellhorn.example.com

secrets:
  secretKey: "your-secret-key-must-be-at-least-32-characters-long"
  fuellhornSecret: "your-fuellhorn-secret-must-be-at-least-32-chars"
```

### PostgreSQL with External Database

```yaml
database:
  type: postgresql
  external:
    host: postgres.database.svc.cluster.local
    port: 5432
    database: fuellhorn
    username: fuellhorn
    existingSecret: postgres-credentials  # Secret with key "password"

secrets:
  existingSecret: fuellhorn-secrets
```

## Upgrading

```bash
helm upgrade fuellhorn ./charts/fuellhorn --values my-values.yaml
```

## Uninstalling

```bash
helm uninstall fuellhorn
```

**Note:** PVCs are not automatically deleted. To remove data:

```bash
kubectl delete pvc fuellhorn-data
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=fuellhorn
```

### View Logs

```bash
kubectl logs -f deployment/fuellhorn
```

### Check Configuration

```bash
helm get values fuellhorn
```

### Verify Templates

```bash
helm template fuellhorn ./charts/fuellhorn --values my-values.yaml
```
