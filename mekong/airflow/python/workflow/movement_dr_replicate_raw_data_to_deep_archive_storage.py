from __future__ import annotations

import datetime
import pendulum

from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator

from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator

with DAG(
  dag_id="movement_dr_replicate_raw_data_to_deep_archive_storage",
  schedule="0 3 * * *",
  start_date=pendulum.datetime(2024, 8, 8, tz="Asia/Ho_Chi_Minh"),
  catchup=True,
  dagrun_timeout=datetime.timedelta(minutes=60),
  tags=["dr", "replicate", "deep-archived"],
  default_args={"depends_on_past": True},
) as dag:
    
  start_here = EmptyOperator(
    task_id="start_here",
  )

  copy_files = GCSToGCSOperator(
    task_id="copy_files",
    source_bucket="momovn-datalake-sandbox-us-central1-prod",
    source_object="analytics_153024151/events/movement/dt={{ data_interval_start.subtract(days=4).format('YYYY-MM-DD') }}",
    destination_bucket="momovn-datalake-deep-archive-us-central1-prod",
    destination_object="bigquery/gcp/analytics_153024151/events/dt={{ data_interval_start.subtract(days=4).format('YYYY-MM-DD') }}/",
    replace=True,
    match_glob='**/*.parquet'
  )

  start_here >> copy_files

if __name__ == "__main__":
  dag.test()