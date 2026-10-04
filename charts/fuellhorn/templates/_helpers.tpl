{{/*
Expand the name of the chart.
*/}}
{{- define "fuellhorn.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "fuellhorn.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "fuellhorn.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "fuellhorn.labels" -}}
helm.sh/chart: {{ include "fuellhorn.chart" . }}
{{ include "fuellhorn.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "fuellhorn.selectorLabels" -}}
app.kubernetes.io/name: {{ include "fuellhorn.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Image reference: image.tag, sonst appVersion des Charts (#377)
*/}}
{{- define "fuellhorn.image" -}}
{{- printf "%s:%s" .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) }}
{{- end }}

{{/*
Database URL for PostgreSQL (Passwort URL-kodiert, #377)
*/}}
{{- define "fuellhorn.databaseUrl" -}}
{{- $host := required "database.external.host muss gesetzt sein (oder database.external.existingSecret verwenden)" .Values.database.external.host }}
{{- $password := required "database.external.password muss gesetzt sein (oder database.external.existingSecret verwenden)" .Values.database.external.password }}
{{- printf "postgresql://%s:%s@%s:%d/%s" .Values.database.external.username ($password | urlquery) $host (int .Values.database.external.port) .Values.database.external.database }}
{{- end }}

{{/*
"true", wenn Migrationen als Helm-Hook-Job laufen (nur PostgreSQL; SQLite nutzt den Init-Container am RWO-Volume)
*/}}
{{- define "fuellhorn.migrationJobEnabled" -}}
{{- if and .Values.migrations.job.enabled (eq .Values.database.type "postgresql") }}true{{- end }}
{{- end }}

{{/*
Datenbank-Umgebung für App- und Init-Container
*/}}
{{- define "fuellhorn.databaseEnv" -}}
- name: DB_TYPE
  value: {{ .Values.database.type | quote }}
{{- if eq .Values.database.type "postgresql" }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.database.external.existingSecret | default (printf "%s-db" (include "fuellhorn.fullname" .)) }}
      key: url
{{- else }}
# SQLite-Datei explizit ins Volume, sonst landet sie im site-packages des Containers (#371)
- name: FUELLHORN_DATA_DIR
  value: /app/data
# Login-Sitzungen (NiceGUI-Storage) ebenfalls auf dem Volume, sonst meldet jeder Neustart alle ab (#429)
- name: NICEGUI_STORAGE_PATH
  value: /app/data/.nicegui
{{- end }}
{{- end }}

{{/*
Session-Secret der App (signiert Cookies)
*/}}
{{- define "fuellhorn.secretEnv" -}}
- name: FUELLHORN_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.secrets.existingSecret | default (printf "%s-secrets" (include "fuellhorn.fullname" .)) }}
      key: fuellhorn-secret
{{- end }}

{{/*
Volume-Mount für die SQLite-Daten
*/}}
{{- define "fuellhorn.dataVolumeMount" -}}
{{- if eq .Values.database.type "sqlite" }}
volumeMounts:
  - name: data
    mountPath: /app/data
{{- end }}
{{- end }}
