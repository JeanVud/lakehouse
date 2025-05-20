from __future__ import annotations

import logging
import pendulum
import pytz

from datetime import datetime, timedelta
from croniter import croniter

from airflow.models.dag import DAG
from airflow.utils.task_group import TaskGroup
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator

from mekong.movement.python.common import WhiteLists
from mekong.movement.python.bigquery import BigQuery
from mekong.movement.python.migration import Migration

with DAG(
  dag_id="00_movement_cron_trigger_data_sync_controller",
  schedule="*/15 * * * *",
  start_date=pendulum.datetime(2024, 5, 29, tz="UTC"),
  catchup=True,
  max_active_runs=1,
  max_active_tasks=20,
  dagrun_timeout=timedelta(minutes=60),
  tags=["trigger", "controller", "cron"],
  default_args={"retries": 2},
) as dag:
  
  whitelists = WhiteLists()
  logger = logging.getLogger(__name__)
  
  for dataset in whitelists.datasets:
    dataset_name = dataset.name.lower()

    for table in dataset.tables:
      table_name = table.name.lower()
      table_name_fqn_id = table.name_fqn_id
      origin_table_name_fqn = table.origin_name_fqn

      tg_id = table.name_fqn_id.replace(".", "__")
      cron_schedule = table.schedule

      if cron_schedule == "":
        continue

      with TaskGroup(tg_id) as tg:

        def check_if_need_data_sync(cron_schedule, data_interval_start, data_interval_end, logical_date, ti, **kwargs):
          # can not access task_group id directly in code because the last one overwrite all, must be access via function scope
          task_group_id = ti.task_id.split(".")[0]

          tz = pytz.timezone("Asia/Ho_Chi_Minh")
          data_interval_start_dt = datetime.fromisoformat(data_interval_start.to_datetime_string())
          data_interval_end_dt = datetime.fromisoformat(data_interval_end.to_datetime_string())
          _from = tz.localize(data_interval_start_dt + timedelta(hours = 7))
          _to = tz.localize(data_interval_end_dt + timedelta(hours = 7) - timedelta(seconds=1))

          logger.info(f"logical_date: {logical_date}")
          logger.info(f"logical_date with timezone: {logical_date.in_timezone('Asia/Ho_Chi_Minh')}")
          logger.info(f"data_interval_start: {data_interval_start}")
          logger.info(f"data_interval_end: {data_interval_end}")
          logger.info(f"_from with timezone: {_from}")
          logger.info(f"_to with timezone: {_to}")
          logger.info(f"cron_schedule: {cron_schedule}")

          is_match = croniter.match_range(cron_schedule, _from, _to)
          if is_match:
            return f"{task_group_id}.run_trigger"
          
          return None
        
        check_if_need_data_sync = BranchPythonOperator(
          task_id='check_if_need_data_sync',
          python_callable=check_if_need_data_sync,
          op_kwargs={"cron_schedule": cron_schedule},
        )

        if origin_table_name_fqn.endswith("YYYYMMDD"):
          origin_table_name_fqn = origin_table_name_fqn.replace("_YYYYMMDD", "_{{ logical_date.in_timezone('Asia/Ho_Chi_Minh').subtract(days=1).format('YYYYMMDD') }}")
          
        trigger_dag = TriggerDagRunOperator(
          task_id="run_trigger",
          reset_dag_run=True, # all dag run for the same logical date will be clean by https://github.com/apache/airflow/blob/79cf7e0609ef0640088ee80117e95046fa48063b/airflow/operators/trigger_dagrun.py#L207
          wait_for_completion=False,
          trigger_dag_id=table_name_fqn_id,
          trigger_run_id="{{ logical_date.isoformat() }}",
          logical_date="{{ logical_date.isoformat() }}",
          conf={
            "name": table_name_fqn_id,
            "origin": origin_table_name_fqn,
            "partition_id": "{{ logical_date.in_timezone('Asia/Ho_Chi_Minh').subtract(days=1).format('YYYYMMDD') }}",
            "schedule": "cron"
          }
        )

        check_if_need_data_sync >> trigger_dag

      
      
