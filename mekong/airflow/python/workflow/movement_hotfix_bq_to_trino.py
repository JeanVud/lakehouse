import pendulum

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import BigQueryToGCSOperator
from mekong.movement.python.operators import SparkSQLExecuteQueryOperator

ARGS = {
    'owner': 'vinh.dang',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2024, 12, 11, tz="Asia/Ho_Chi_Minh"),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True
}

with DAG(
    dag_id='movement_hotfix_bq_to_trino',
    schedule_interval='5 * * * *',
    default_args=ARGS,
    tags=['APP_EVENT_V7'],
    description=None,
    catchup=True
) as dag: 

    bigquery_to_gcs = BigQueryToGCSOperator(
        task_id="bigquery_to_gcs",
        project_id="momovn-data-platform",
        source_project_dataset_table="momovn-data-platform.APP_VARZ.APP_EVENT_V7${{ logical_date.format('YYYYMMDDHH') }}",
        destination_cloud_storage_uris=["gs://momovn-datalake-movement-us-central1-prod/gcp/bigquery/momovn-data-platform/APP_VARZ/APP_EVENT_V7/dt={{ logical_date.add(hours=7) | ds }}/hh={{ logical_date.add(hours=7).format('HH') }}/*.parquet"],
        compression="ZSTD",
        export_format="PARQUET",
        force_rerun=True
    )

    spark_sql_job = SparkSQLExecuteQueryOperator(
        spark_conn_id="kyuubi_spark_sql_conn",
        sql="""
          insert overwrite analytics.app_varz.app_event_v4 PARTITION (_partitiontime = '{{ logical_date.add(hours=7) | ds }}', hh = '{{ logical_date.add(hours=7).format("HH") }}')
          select 
            event_name, user_id, agent_id, event_params, timestamp, app_info,
              named_struct(
                'category', device_info.category,
                'mobile_brand_name', device_info.mobile_brand_name,
                'mobile_model_name', device_info.mobile_model_name,
                'operating_system', device_info.operating_system,
                'operating_system_version', device_info.operating_system_version
              ) as device_info,
            location, momo_session_id,
            mini_app_id, event_id, hash_code, server_timestamp, device_pseudo_id, user_pseudo_id, momo_session_id_v2,
            offset_base, offset, attribution_id
          from parquet.`gs://momovn-datalake-movement-us-central1-prod/gcp/bigquery/momovn-data-platform/APP_VARZ/APP_EVENT_V7/dt={{ logical_date.add(hours=7) | ds }}/hh={{ logical_date.add(hours=7).format('HH') }}/*.parquet`
        """,
        task_id="spark_sql_job",
        conf=[
            "set `spark.sql.iceberg.distribution-mode`=`none`",
            "set `spark.sql.sources.partitionOverwriteMode`=`dynamic`"
        ]
    )

    bigquery_to_gcs >> spark_sql_job
