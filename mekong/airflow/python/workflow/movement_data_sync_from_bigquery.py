import pendulum
import logging

from datetime import timedelta

from airflow.decorators import dag, task, task_group
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTableExistenceSensor
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTablePartitionExistenceSensor
from airflow.operators.empty import EmptyOperator

from mekong.movement.python.common import WhiteLists, MigrationMapper
from mekong.movement.python.migration import Migration

whitelists = WhiteLists()

for dataset in whitelists.datasets:
  dataset_name = dataset.name.lower()

  for table in dataset.tables:
    table_name = table.name.lower()
    table_name_fqn_id = table.name_fqn_id
    table_sensor = table.sensor
    table_backfilling = table.backfilling

    @dag(
      dag_id=table_name_fqn_id,
      schedule=None,
      start_date=pendulum.datetime(1999, 1, 1, tz="UTC"),
      catchup=False,
      max_active_runs=1,
      is_paused_upon_creation=False,
      tags=["movement", dataset_name, table_name],
      default_args={"retries": 2},
    )
    def movement_data_sync_from_bigquery():

        tableMapper = MigrationMapper()
        logger = logging.getLogger(__name__)

        @task_group(group_id=table_name)
        def sync_table():
          
          if table_sensor == "":
            sensor = EmptyOperator(task_id="no_sensor")
          elif table_sensor == "partitioning":
            sensor = BigQueryTablePartitionExistenceSensor(
              task_id="sensor",
              project_id="{{ dag_run.conf.get('origin').split('.')[0] }}",
              dataset_id="{{ dag_run.conf.get('origin').split('.')[1] }}",
              table_id="{{ dag_run.conf.get('origin').split('.')[2] }}",
              partition_id="{{ dag_run.conf.get('partition_id') }}",
              poke_interval=600,
              mode="reschedule",
              timeout=timedelta(days=1)
            )
          else:
            sensor = BigQueryTableExistenceSensor(
              task_id="sensor",
              project_id="{{ dag_run.conf.get('origin').split('.')[0] }}",
              dataset_id="{{ dag_run.conf.get('origin').split('.')[1] }}",
              table_id="{{ dag_run.conf.get('origin').split('.')[2] }}",
              poke_interval=600,
              mode="reschedule",
              timeout=timedelta(days=1)
            )

          @task
          def sync_data_from_bigquery_to_datalake(dag, **kwargs):
            logger.info(kwargs)

            whitelists = WhiteLists()
            config_spec = whitelists.get_whitelist_config_for_table(dag.dag_id)
            rename_to = config_spec.rename_to
            force_kind = config_spec.kind

            fqn_origin_table_name = kwargs['dag_run'].conf.get('origin')
            fqn_target_table_name = kwargs['dag_run'].conf.get('name')

            fqn_lake_table_name = rename_to if rename_to != "" else None
            trigger_partition_id = kwargs['dag_run'].conf.get('partition_id')
            
            # current support backfilling for YYYYMMDD sharding only
            if fqn_target_table_name.lower().endswith("yyyymmdd"):
              period = int(kwargs["period"]) if "period" in kwargs else 0
              partition_id = pendulum.from_format(trigger_partition_id, 'YYYYMMDD').add(days=period).format('YYYYMMDD')
              fqn_origin_table_name = fqn_origin_table_name.replace(trigger_partition_id, partition_id)
            else:
              partition_id = trigger_partition_id

            logger.info(f"fqn_target_table_name: {fqn_target_table_name}")
            logger.info(f"fqn_origin_table_name: {fqn_origin_table_name}")
            logger.info(f"rename_to: {rename_to}")
            logger.info(f"kind: {force_kind}")

            logger.info(f"sync from {fqn_origin_table_name} to {fqn_lake_table_name} for partition id: {partition_id}")

            migration = Migration()

            if force_kind == "":
              # TODO: refactor flow sync table with the same name
              # for sharding table, replace sharding pattern with sharding id
              fqn_origin_table_name = fqn_origin_table_name.replace("yyyymmdd", partition_id)
              migration.sync_table_from_bigquery(
                fqn_origin_table_name,
                fqn_lake_table_name,
                date=partition_id,
                enable_insert_override=config_spec.enable_insert_override
              )
            elif force_kind == "normal-table":
              migration.force_sync_partitions_as_normal_table(fqn_origin_table_name, fqn_lake_table_name, date=partition_id)

            return f"synced data for {kwargs['dag_run'].conf}"
          
          backfill_periods = [] if table_backfilling == "" else table_backfilling.split(",")
          backfill_arr = []

          for p in backfill_periods:
            backfill_arr.append(sync_data_from_bigquery_to_datalake.override(task_id=f"backfill{p}")(period=p))

          sync_data_from_bigquery_to_datalake = sync_data_from_bigquery_to_datalake()

          sensor >> sync_data_from_bigquery_to_datalake
          backfill_arr

        sync_table()

    movement_data_sync_from_bigquery()