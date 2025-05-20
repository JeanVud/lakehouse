from __future__ import annotations

import datetime
import pendulum

from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.gcs import GCSDeleteObjectsOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryDeleteTableOperator

with DAG(
  dag_id="movement_gc_clean_tombstones_data",
  schedule="0 3 * * *",
  start_date=pendulum.datetime(2024, 8, 8, tz="Asia/Ho_Chi_Minh"),
  catchup=True,
  dagrun_timeout=datetime.timedelta(minutes=60),
  tags=["gc", "cleasing", "tombstones"]
) as dag:
    
  start_here = EmptyOperator(
    task_id="start_here"
  )

  # delete data on Big Query
  delete_on_bq = BigQueryDeleteTableOperator(
    task_id="delete_on_bq",
    deletion_dataset_table="project-5400504384186300846.analytics_153024151.events_{{ data_interval_start.subtract(days=10).format('YYYYMMDD') }}",
    location="US"
  )

  # remove data on GCS (Lakehouse)
  delete_on_gcs = GCSDeleteObjectsOperator(
    task_id="delete_on_gcs",
    bucket_name="momovn-datalake-sandbox-us-central1-prod",
    prefix="analytics_153024151/events/movement/dt={{ data_interval_start.subtract(days=45).format('YYYY-MM-DD') }}"
  )

  start_here >> delete_on_gcs >> delete_on_bq


if __name__ == "__main__":
  dag.test()