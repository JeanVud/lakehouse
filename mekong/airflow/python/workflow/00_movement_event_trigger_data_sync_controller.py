from __future__ import annotations

import logging
import pendulum

from datetime import datetime, timedelta

from airflow.models.dag import DAG
from airflow.datasets import Dataset
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator

from mekong.movement.python.common import WhiteLists
from mekong.movement.python.bigquery import BigQuery
from mekong.movement.python.migration import Migration

with DAG(
  dag_id="00_movement_event_trigger_data_sync_controller",
  start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
  catchup=False,
  schedule=[Dataset(f"bigquery://datalake/movement/datasync")],
  is_paused_upon_creation=False,
  max_active_runs=128,
  max_active_tasks=64,
  tags=["trigger", "controller", "event"],
  default_args={"retries": 2},
) as dag:
  
  def get_partitions_change_from_triggering_events(triggering_dataset_events=None, **kwargs):
    logger = logging.getLogger(__name__)
    whitelists = WhiteLists()
    bq = BigQuery()
    migration = Migration()

    for dataset_uri, dataset_events in triggering_dataset_events.items():
      
      partitions = []

      for event in dataset_events:
        payload = event.extra
        timestamp = event.timestamp
        # 2024-07-04T04:40:24
        msg_publish_time = datetime.strptime(payload['publishTime'][:19], "%Y-%m-%dT%H:%M:%S")
        logger.info(f"get trigger event data information {payload} publish at {msg_publish_time}")
        fqn_original_table_name = f"{payload['projectId']}.{payload['datasetId']}.{payload['tableId']}"
        
        # quick check for whitelisting
        sharding_spec = migration.detect_sharding_spec(fqn_original_table_name)
        logger.info(f"sharding spec: {sharding_spec}")
        fqn_table_name_id = sharding_spec["name"].lower()

        # change table identity for sharding table
        if sharding_spec["is_sharded"]:
          fqn_table_name_id = f"{fqn_table_name_id}_yyyymmdd"

        if not whitelists.is_allowed(fqn_table_name_id):
          logger.info(f"table {fqn_table_name_id} is not whitelisted yet")
          continue
        
        if whitelists.is_scheduled_table(fqn_table_name_id):
          logger.info(f"table {fqn_table_name_id} had been configured with a schedule, ingored by trigger event")
          continue
        
        table_spec = migration.analyze_table_spec(fqn_original_table_name)
        kind = table_spec["kind"]
        
        match kind:
          case "normal-table":
            run_id = timestamp.strftime("%Y%m%d%H%M%S")
            date = timestamp.strftime("%Y-%m-%d")
            virtual_partition_id = timestamp.strftime("%Y%m%d")

            virtual_partition = {
              "trigger_dag_id": fqn_table_name_id,
              "trigger_run_id": run_id,
              "logical_date": date,
              "conf": {
                "name": fqn_table_name_id,
                "kind": "non-partitioned",
                "origin": fqn_original_table_name,
                "partition_id": virtual_partition_id
              }
            }
            
            partitions.append(virtual_partition)
          case "sharded-table":
            run_id = table_spec["meta"]["shard"]
            date = datetime.strptime(run_id, "%Y%m%d").strftime("%Y-%m-%d")

            partition = {
              "trigger_dag_id": fqn_table_name_id,
              "trigger_run_id": run_id,
              "logical_date": date,
              "conf": {
                "name": fqn_table_name_id,
                "kind": "sharded",
                "origin": fqn_original_table_name,
                "partition_id": run_id
              }
            }
            
            partitions.append(partition)
          case "partitioned-table":

            if whitelists.is_force_sync_full_table(fqn_table_name_id):
              p = {
                "trigger_dag_id": fqn_table_name_id,
                "trigger_run_id": msg_publish_time.strftime("%Y%m%d"),
                "logical_date": msg_publish_time.strftime("%Y-%m-%d"),
                "conf": {
                  "name": fqn_table_name_id,
                  "kind": "partitioned",
                  "origin": fqn_original_table_name,
                  "partition_id": msg_publish_time.strftime("%Y%m%d")
                }
              }

              partitions.append(p)
              continue

            modified_from = msg_publish_time - timedelta(minutes=10)
            num, table_partitions = bq.get_table_partitions_from_time(fqn_original_table_name, modified_from)

            if num > 10:
              # TODO: switch to sync full table
              logger.error('Total partitions changed execced maximum 10 partitions')
              continue
            
            logger.info(f"total partition change {num}")

            for partition in table_partitions:
              partition_id = partition["partition_id"]
              run_id = partition_id

              # TODO: generate date from partition id
              if partition_id == "__NULL__":
                run_id = "20000101"
                date = datetime.strptime(run_id, "%Y%m%d").strftime("%Y-%m-%d")
              elif partition_id == "__UNPARTITIONED__":
                run_id = "20000102"
                date = datetime.strptime(run_id, "%Y%m%d").strftime("%Y-%m-%d")
              else:
                date = migration.generate_date_from_partition_id(partition_id)
                logger.info(f"partition_id {partition_id}, date {date}")

              p = {
                "trigger_dag_id": fqn_table_name_id,
                "trigger_run_id": run_id,
                "logical_date": date,
                "conf": {
                  "name": fqn_table_name_id,
                  "kind": "partitioned",
                  "origin": fqn_original_table_name,
                  "partition_id": partition_id
                }
              }
              
              partitions.append(p)

      return partitions
  
  get_partitions_change_from_triggering_events = PythonOperator(task_id="get_partitions_change_from_triggering_events", python_callable=get_partitions_change_from_triggering_events)
  
  TriggerDagRunOperator.partial(
    task_id="trigger_dagrun",
    reset_dag_run=True, # all dag run for the same logical date will be clean by https://github.com/apache/airflow/blob/79cf7e0609ef0640088ee80117e95046fa48063b/airflow/operators/trigger_dagrun.py#L207
    wait_for_completion=False,
    map_index_template="""{{ task.conf['name'] }}""",
  ).expand_kwargs(get_partitions_change_from_triggering_events.output)
