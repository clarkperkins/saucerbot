{{- define "saucerbot.backendName" -}}
{{- printf "%s-backend" (include "saucerbot.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "saucerbot.backendSelectorLabels" -}}
{{ include "saucerbot.commonSelectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{- define "saucerbot.backendLabels" -}}
{{ include "saucerbot.backendSelectorLabels" . }}
{{ include "saucerbot.otherLabels" . }}
{{- end }}
