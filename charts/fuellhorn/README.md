# Fuellhorn Helm Chart

Self-hosted food inventory management for Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2+
- PV provisioner support (for SQLite persistence)

## Installation

### From OCI Registry (Recommended)

The chart is published to GitHub Container Registry:

```bash
# Install latest version
helm install fuellhorn oci://ghcr.io/jensens/fuellhorn \
  --set secrets.secretKey="your-secret-key-min-32-chars-here" \
  --set secrets.fuellhornSecret="your-fuellhorn-secret-min-32-chars"

# Install specific version
helm install fuellhorn oci://ghcr.io/jensens/fuellhorn --version 0.2.0

# With custom values file
helm install fuellhorn oci://ghcr.io/jensens/fuellhorn -f my-values.yaml
```

### From Git (Development)

```bash
git clone https://github.com/jensens/fuellhorn.git
helm install fuellhorn ./fuellhorn/charts/fuellhorn \
  --set secrets.secretKey="your-secret-key-min-32-chars-here" \
  --set secrets.fuellhornSecret="your-fuellhorn-secret-min-32-chars"
```

### GitOps with ArgoCD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: fuellhorn
spec:
  source:
    chart: fuellhorn
    repoURL: ghcr.io/jensens
    targetRevision: 0.2.0
    helm:
      values: |
        secrets:
          existingSecret: fuellhorn-secrets
        database:
          type: postgresql
          external:
            host: postgres.example.com
            existingSecret: postgres-credentials
  destination:
    server: https://kubernetes.default.svc
    namespace: fuellhorn
```

### Production with PostgreSQL

```bash
helm install fuellhorn oci://ghcr.io/jensens/fuellhorn \
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
helm install fuellhorn oci://ghcr.io/jensens/fuellhorn \
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

### Init Containers

| Parameter | Description | Default |
|-----------|-------------|---------|
| `initContainers.migrations.enabled` | Run Alembic migrations on startup | `true` |
| `initContainers.adminUser.enabled` | Create initial admin user | `false` |
| `initContainers.adminUser.username` | Admin username | `admin` |
| `initContainers.adminUser.email` | Admin email | `admin@fuellhorn.local` |
| `initContainers.adminUser.password` | Admin password (not recommended for production) | `""` |
| `initContainers.adminUser.existingSecret` | Secret name with key `admin-password` | `""` |

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

### GitOps-Friendly Deployment with Auto-Created Admin

For fully automated deployments (e.g., with ArgoCD), you can enable automatic admin user creation:

```yaml
database:
  type: postgresql
  external:
    host: postgres.database.svc.cluster.local
    existingSecret: postgres-credentials

secrets:
  existingSecret: fuellhorn-secrets

initContainers:
  migrations:
    enabled: true  # Runs Alembic migrations automatically
  adminUser:
    enabled: true
    username: admin
    email: admin@example.com
    existingSecret: fuellhorn-admin  # Secret with key "admin-password"
```

Create the admin password secret:

```bash
kubectl create secret generic fuellhorn-admin \
  --from-literal=admin-password='your-secure-password'
```

## Upgrading

```bash
# From OCI registry
helm upgrade fuellhorn oci://ghcr.io/jensens/fuellhorn -f my-values.yaml

# From local checkout
helm upgrade fuellhorn ./charts/fuellhorn -f my-values.yaml
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
# Pull chart first for template verification
helm pull oci://ghcr.io/jensens/fuellhorn --untar
helm template fuellhorn ./fuellhorn -f my-values.yaml
```
