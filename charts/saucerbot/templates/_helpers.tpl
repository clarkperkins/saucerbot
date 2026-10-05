{{/*
Expand the name of the chart.
*/}}
{{- define "saucerbot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "saucerbot.fullname" -}}
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
{{- define "saucerbot.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "saucerbot.commonSelectorLabels" -}}
app.kubernetes.io/name: {{ include "saucerbot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "saucerbot.otherLabels" -}}
helm.sh/chart: {{ include "saucerbot.chart" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "saucerbot.commonLabels" -}}
{{ include "saucerbot.commonSelectorLabels" . }}
{{ include "saucerbot.otherLabels" . }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "saucerbot.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "saucerbot.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
DATABASE_URL, from a secret the operator manages outside this release.
`required` turns a missing value into a template error naming the key, instead
of pods that start and then crash-loop on a missing setting.
*/}}
{{- define "saucerbot.databaseEnv" -}}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ required "postgres.existingSecret is required: this chart does not deploy a database" .Values.postgres.existingSecret }}
      key: {{ required "postgres.secretKey is required" .Values.postgres.secretKey }}
{{- end }}

{{/*
envFrom for the migrate job, defaulting to the backend's so migrations cannot
silently run with different configuration than the app. Renders to nothing
when both are empty, so the job gets no envFrom key at all.
*/}}
{{- define "saucerbot.migrateEnvFrom" -}}
{{- with (.Values.migrate.envFrom | default .Values.backend.envFrom) -}}
{{- toYaml . -}}
{{- end -}}
{{- end }}
