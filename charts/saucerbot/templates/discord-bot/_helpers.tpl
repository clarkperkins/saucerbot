{{- define "saucerbot.discordBotName" -}}
{{- printf "%s-discord-bot" (include "saucerbot.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "saucerbot.discordBotSelectorLabels" -}}
{{ include "saucerbot.commonSelectorLabels" . }}
app.kubernetes.io/component: discord-bot
{{- end }}

{{- define "saucerbot.discordBotLabels" -}}
{{ include "saucerbot.discordBotSelectorLabels" . }}
{{ include "saucerbot.otherLabels" . }}
{{- end }}
