FROM apache/airflow:slim-2.10.0-python3.10

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl \
  libpq-dev libsasl2-dev \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
  
USER airflow

COPY airflow/dockerfiles/requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

COPY movement /opt/airflow/mekong/movement
COPY airflow/python/workflow /opt/airflow/dags/ 
