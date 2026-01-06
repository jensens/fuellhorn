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
Database URL for PostgreSQL
*/}}
{{- define "fuellhorn.databaseUrl" -}}
{{- if .Values.database.external.existingSecret }}
{{- /* Will be populated from existing secret */ -}}
{{- else }}
{{- printf "postgresql://%s:%s@%s:%d/%s" .Values.database.external.username .Values.database.external.password .Values.database.external.host (int .Values.database.external.port) .Values.database.external.database }}
{{- end }}
{{- end }}
