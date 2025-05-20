CREATE DATABASE {{ .Values.database.dbname | default "grist" }};
CREATE USER {{ .Values.database.username | default "grist" }} WITH PASSWORD '{{ .Values.database.password | default "grist" }}';