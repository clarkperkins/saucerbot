{{- define "saucerbot.migrateName" -}}
{{- printf "%s-migrate" (include "saucerbot.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "saucerbot.migrateSelectorLabels" -}}
{{ include "saucerbot.commonSelectorLabels" . }}
app.kubernetes.io/component: migrate
{{- end }}

{{- define "saucerbot.migrateLabels" -}}
{{ include "saucerbot.migrateSelectorLabels" . }}
{{ include "saucerbot.otherLabels" . }}
{{- end }}
