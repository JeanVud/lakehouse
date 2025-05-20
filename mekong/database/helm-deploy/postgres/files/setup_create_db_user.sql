CREATE DATABASE {{ .Values.database.dbname | default "airflow" }};
CREATE USER {{ .Values.database.username | default "airflow" }} WITH PASSWORD '{{ .Values.database.password | default "airflow" }}';