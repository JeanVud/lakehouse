import os
import logging
import click
import re

import pendulum

from google.cloud import bigquery
from google.cloud.bigquery.table import RangePartitioning, TimePartitioning
from google.api_core.exceptions import NotFound

from mekong.movement.python.singleton_meta import SingletonMeta
from mekong.movement.python.common import CliContext

from mekong.movement.python.spark import Spark
from mekong.movement.python.bigquery import BigQuery
from mekong.movement.python.gcs import Gcs
from mekong.movement.python.common import MigrationMapper, WhiteLists

class Migration(metaclass=SingletonMeta):

  def __init__(self):
    self.spark = Spark()
    self.bq = BigQuery()
    self.gcs = Gcs()
    self.mapper = MigrationMapper()
    self.whitelists = WhiteLists()
    self.context = CliContext()
    self.log = logging.getLogger(__name__)

  def get_datalake_table_from_bq_fqn(self, bq_table_fqn):
    return self.mapper.get_datalake_table_from_bq_fqn(bq_table_fqn)

  def generate_series(self, start, end):
    if len(start) != len(end):
      self.log.error("start date: {start} and end date: {end} is not the same pattern")
      return []

    match len(start):
      case 4:
        # year
        year_list = [str(x) for x in range(int(start), int(end) + 1, 1)]
        return year_list
      case 6:
        # month
        start = pendulum.from_format(f"{start}01", 'YYYYMMDD')
        end = pendulum.from_format(f"{end}01", 'YYYYMMDD')
        interval = end - start
        month_list = [start.add(months=x).format('YYYYMM') for x in range(interval.in_months())]
        return month_list
      case 8:
        # day
        start = pendulum.from_format(start, 'YYYYMMDD')
        end = pendulum.from_format(end, 'YYYYMMDD')
        interval = end - start
        date_list = [start.add(days=x).format('YYYYMMDD') for x in range(interval.in_days())]
        return date_list
      case 10:
        # hour
        start = pendulum.from_format(start, 'YYYYMMDDHH')
        end = pendulum.from_format(end, 'YYYYMMDDHH')
        interval = end - start
        hour_list = [start.add(hours=x).format('YYYYMMDDHH') for x in range(interval.in_hours())]
        return hour_list

    return []

  def is_valid_date_for_meta_type(self, type_, date):
    match type_:
      case "DAY":
        return True if len(date) == 8 else False
      case "YEAR":
        return True if len(date) == 4 else False
      case "MONTH":
        return True if len(date) == 6 else False
      case "HOUR":
        return True if len(date) == 10 else False

  def detect_partition_columns_from_partition_id(self, partition_id):
    match len(partition_id):
      case 4:
        return "yyyy"
      case 6:
        return "mm"
      case 8:
        return "dt"
      case 10:
        return "dt,hh"

  def decode_partition_id_to_hive_partition(self, partition_id):
    hive_partition = {}
    match len(partition_id):
      case 4:
        hive_partition = {"yyyy": partition_id}
      case 6:
        hive_partition = {"mm": partition_id[:4] + '-' + partition_id[4:]}
      case 8:
        hive_partition = {"dt": partition_id[:4] + '-' + partition_id[4:6] + '-' + partition_id[6:]}
      case 10:
        hive_partition = {
          "dt": partition_id[:4] + '-' + partition_id[4:6] + '-' + partition_id[6:8],
          "hh": partition_id[8:]
        }

    return hive_partition
  
  def generate_date_from_partition_id(self, partition_id):
     match len(partition_id):
      case 4:
        return f"{partition_id}-01-01"
      case 6:
        return partition_id[:4] + "-" + partition_id[4:] + "-01"
      case 8:
        return partition_id[:4] + "-" + partition_id[4:6] + "-" + partition_id[6:]
      case 10:
        return partition_id[:4] + "-" + partition_id[4:6] + "-" + partition_id[6:8] + " " + partition_id[8:10] + ":00:00"
       
  def get_special_partition_mapping(self, partition_id):

    if partition_id == "__NULL__":
      return "20000101"
    elif partition_id == "__UNPARTITIONED__":
      return "20000102"
    else:
      return partition_id


  def generate_hive_partition_for_partition_spec(self, source_table_target_location, table_spec=None, partition_id=None, overrides=None):

    hive_partition = self.decode_partition_id_to_hive_partition(partition_id)

    type_ = table_spec["meta"]["type"]

    if overrides is not None and overrides.get("type"):
      type_ = overrides["type"]

    match type_:
      case "YEAR":
        return f"{source_table_target_location}/yyyy={hive_partition['yyyy']}/*.parquet"
      case "MONTH":
        return f"{source_table_target_location}/mm={hive_partition['mm']}/*.parquet"
      case "DAY":
        return f"{source_table_target_location}/dt={hive_partition['dt']}/*.parquet"
      case "HOUR":
        return f"{source_table_target_location}/dt={hive_partition['dt']}/hh={hive_partition['hh']}/*.parquet"

  def detect_sharding_spec(self, table):
    sharding_pattern = re.compile("^(.*)_([0-9]{8})$")
    m = sharding_pattern.match(table)
    if m:
      return {"is_sharded": True, "name": m.group(1), "shard": m.group(2), "type": "DAY", "field": "dt"}
    return {"is_sharded": False, "name": table, "shard": None, "type": None, "field": None}

  def get_source_table_target(self, source_table, storage_dest):
    return f"{storage_dest}/{source_table.replace('.', '/')}"

  def get_target_files_pattern(self, table_spec, partition_id=None, overrides=None):
    gcs_dest = self.gcs.get_migration_data_gcs_location()
    fqn_source_table_name = table_spec["fqn_table_name_original_standarized"]

    source_table_target_location = self.get_source_table_target(fqn_source_table_name, gcs_dest)
    kind = table_spec["kind"]
    if kind == "sharded-table":
      fqn_iceberg_table = table_spec["fqn_iceberg_table"]
      source_table_target_location = self.spark.generate_target_location_for_sharding_table(fqn_iceberg_table)
      source_table_target_location = f"{source_table_target_location}/movement"

    target_files_pattern = self.generate_hive_partition_for_partition_spec(source_table_target_location, table_spec, partition_id, overrides)
    return target_files_pattern

  def analyze_table_spec(self, source_table):
    fqn_original_table_name = source_table
    fqn_original_table_name_lower = fqn_original_table_name.lower()
    fqn_iceberg_table = self.mapper.get_datalake_table_from_bq_fqn(fqn_original_table_name_lower)

    partition_spec = self.bq.get_partition_spec(fqn_original_table_name)
    sharding_spec = self.detect_sharding_spec(fqn_original_table_name)

    spec = {}
    spec["fqn_table_name_original"] = fqn_original_table_name
    spec["fqn_table_name_original_standarized"] = fqn_original_table_name
    spec["kind"] = "unknown"
    spec["meta"] = {}

    # act as normal table
    if partition_spec is None and not sharding_spec["is_sharded"]:
      spec["fqn_table_name_id"] = fqn_original_table_name_lower
      spec["fqn_iceberg_table"] = fqn_iceberg_table
      spec["is_sharded"] = False
      spec["is_partitioned"] = False
      spec["meta"]["type"] = "DAY"
      spec["meta"]["fmt"] = "yyyyMMdd"
      spec["kind"] = "normal-table"
    # act as sharded table
    elif partition_spec is None and sharding_spec["is_sharded"]:
      spec["fqn_table_name_id"] = sharding_spec["name"].lower()
      spec["fqn_table_name_original_standarized"] = sharding_spec["name"]
      spec["fqn_iceberg_table"] = fqn_iceberg_table[:-9] # *.*.agent_ref_correctness_20240616 -> *.*.agent_ref_correctness
      spec["is_sharded"] = True
      spec["is_partitioned"] = False
      spec["meta"]["shard"] = sharding_spec["shard"]
      spec["meta"]["type"] = sharding_spec["type"]
      spec["meta"]["fmt"] = "yyyyMMdd"
      spec["kind"] = "sharded-table"
    # sharding and partitioning at the same time
    elif partition_spec and sharding_spec["is_sharded"]:
      self.log.warn(f"detect table {source_table} matching for both sharding and partitioning, act as sharded table")
      # current treat as sharding table first
      spec["fqn_table_name_id"] = sharding_spec["name"].lower()
      spec["fqn_table_name_original_standarized"] = sharding_spec["name"]
      spec["fqn_iceberg_table"] = fqn_iceberg_table[:-9] # *.*.agent_ref_correctness_20240616 -> *.*.agent_ref_correctness
      spec["is_sharded"] = True
      spec["is_partitioned"] = False
      spec["meta"]["shard"] = sharding_spec["shard"]
      spec["meta"]["type"] = sharding_spec["type"]
      spec["meta"]["fmt"] = "yyyyMMdd"
      spec["kind"] = "sharded-table"
    # partitioned table
    elif partition_spec and not sharding_spec["is_sharded"]:
      spec["fqn_table_name_id"] = fqn_original_table_name_lower
      spec["fqn_iceberg_table"] = fqn_iceberg_table
      spec["is_sharded"] = False
      spec["is_partitioned"] = True
      spec["kind"] = "partitioned-table"

      match partition_spec:
        case RangePartitioning():
          self.log.warn("RangePartitioning is not supported, treat as normal table without partition")

          spec["is_sharded"] = False
          spec["is_partitioned"] = False
        case TimePartitioning():
          # https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.table.TimePartitioning
          spec["meta"]["type"] = partition_spec.type_
          spec["meta"]["field"] = partition_spec.field if partition_spec.field else "PARTITIONTIME"

          match spec["meta"]["type"]:
            case "HOUR":  spec["meta"]["fmt"] = "yyyyMMddHH"
            case "DAY":   spec["meta"]["fmt"] = "yyyyMMdd"
            case "MONTH": spec["meta"]["fmt"] = "yyyyMM"
            case "YEAR":  spec["meta"]["fmt"] = "yyyy"

    return spec
  
  def run_export_bq_to_gcs(self, source_table, table_spec, partition_id, target_files_pattern, force_sync_full_table=False):

    if force_sync_full_table:
      source_table_partition_id = f"{source_table}"
      filter_condition = "1 = 1;"
    else:
      source_table_partition_id = f"{source_table}${partition_id}"
      filter_condition = f"FORMAT_DATETIME('%Y%m%d', _PARTITIONTIME) = '{partition_id}';"

    self.log.info(f"sync partition {source_table_partition_id}")

    partition_column = table_spec["meta"]["field"]
    if partition_column == "PARTITIONTIME":

      target_temp_table_ref = f"{source_table.split('.')[2]}_{partition_id}"
      self.log.info(f"_PARTITIONTIME column detected, switching to export partition data with psduedo column {partition_column}")

      export_by_temp_table_query = f"""
        CREATE OR REPLACE TEMPORARY TABLE {target_temp_table_ref}
        AS
        SELECT *, _PARTITIONTIME as PARTITIONTIME
        FROM {source_table}
        WHERE {filter_condition}
        

        EXPORT DATA OPTIONS(
          uri='{target_files_pattern}',
          format='PARQUET',
          overwrite=true
        ) AS
        SELECT *
        FROM {target_temp_table_ref};
      """

      self.bq.run_query(export_by_temp_table_query)
    else:
      self.bq.export_to_gcs(source_table_partition_id, target_files_pattern)

  # sync normal table
  def sync_normal_table_from_bigquery(self, source_table, table_spec, target_table, date=None):
    partition_id = date if date else "19931227"
    target_files_pattern = self.get_target_files_pattern(table_spec, partition_id)

    # delete destination gcs folder before run export
    self.gcs.delete_objects_in_folder(target_files_pattern)
    
    self.bq.export_to_gcs(source_table, target_files_pattern)
    self.spark.truncate_table(target_table)
    self.spark.load(target_files_pattern, target_table, table_spec, use_hive_partitioning=False, create_table_if_not_exist=True)

    self.log.info("-" * 100)
    self.log.info("synchronized:")
    self.log.info(f"-> source: {source_table}")
    self.log.info(f"-> target: {target_table}")
    self.log.info(f"-> date: {date}")

  # force sync as normal table
  def force_sync_partitions_as_normal_table(self, source_table, target_table=None, date=None, use_hive_partitioning=False):
    partition_id = date if date else "19931227"
    table_spec = self.analyze_table_spec(source_table)
    # target_table = self.get_datalake_table_from_bq_fqn(source_table)
    target_table = target_table if target_table else table_spec["fqn_iceberg_table"]

    self.log.info(f"migrating:")
    self.log.info(f"-> source: {source_table}")
    self.log.info(f"-> sink: {target_table}")
    self.log.info(f"-> config: date={date} and use_hive_partitioning={use_hive_partitioning}")
    self.log.info("-" * 100)

    # should be generate partition_id or remove this file pattern
    # table_spec["meta"]["type"] = "DAY"
    target_files_pattern = self.get_target_files_pattern(table_spec, partition_id, overrides = {"type": "DAY"})
    # delete destination gcs folder before run export
    self.gcs.delete_objects_in_folder(target_files_pattern)

    partition_by = self.detect_partition_columns_from_partition_id(partition_id)
    table_spec["meta"]["partition_by"] = partition_by
    
    self.run_export_bq_to_gcs(source_table, table_spec, partition_id, target_files_pattern, force_sync_full_table=True)
    self.spark.create_table_if_not_exist(target_files_pattern, target_table, table_spec, use_hive_partitioning)

    # force insert table is normal table
    table_spec["kind"] = "normal-table"
    self.spark.truncate_table(target_table)
    self.spark.load(target_files_pattern, target_table, table_spec, use_hive_partitioning, create_table_if_not_exist=True)

  # sync 1 shard
  def sync_sharded_table_from_bigquery(self, source_table, table_spec, target_table, shard):
    partition_id = shard
    hive_partition = self.decode_partition_id_to_hive_partition(partition_id)

    self.log.info(f"decode partition_id {partition_id} to hive partition {hive_partition}")
    iso_partition_id = hive_partition["dt"]
    table_spec["meta"]["partition_by"] = "dt"

    target_files_pattern = self.get_target_files_pattern(table_spec, partition_id)

    # delete before export
    self.gcs.delete_objects_in_folder(target_files_pattern)

    self.bq.export_to_gcs(source_table, target_files_pattern)
    self.spark.truncate_hive_partition(target_table, partition_by="dt", iso_partition_id=iso_partition_id)
    self.spark.load(target_files_pattern, target_table, table_spec, use_hive_partitioning=False, create_table_if_not_exist=True)

    self.log.info("-" * 100)
    self.log.info("synchronized:")
    self.log.info(f"-> source: {source_table}")
    self.log.info(f"-> target: {target_table}")
    self.log.info(f"-> shard: {shard}")

  # sync range shards
  def sync_sharded_table_from_bigquery_by_range(self, source_table, table_spec, target_table, from_shard, to_shard):
    self.log.info(f"start syncing {source_table} from BQ to {target_table} for sharding from {from_shard} to {to_shard}")
    shards = []
    self.log.info(f"found total {len(shards)} shards need to be sync")

    for shard in shards:
      self.sync_sharded_table_from_bigquery(source_table, table_spec, target_table, shard)

    self.log.info("=" * 100)
    self.log.info(f"sync table {source_table} done!")

  # sync 1 partition
  def sync_partitioned_table_from_bigquery(self, source_table, table_spec, target_table, partition_id, use_hive_partitioning=False):
    # rewrite two special partitions:
    # __NULL__          -> 19600101
    # __UNPARTITIONED__ -> 19600102
    pseudo_partition_id = self.get_special_partition_mapping(partition_id)
    # always processing as hive partitioning because data layout on gcs must be structured as hive parttioning
    hive_partition = self.decode_partition_id_to_hive_partition(pseudo_partition_id)
    self.log.info(f"decode partition_id {partition_id} to hive partition {hive_partition}")
    partition_key = list(hive_partition.keys())[0]
    iso_partition_id = hive_partition[partition_key]

    partition_by = self.detect_partition_columns_from_partition_id(pseudo_partition_id)
    table_spec["meta"]["partition_by"] = partition_by

    source_table_partition_id = f"{source_table}${partition_id}"
    self.log.info(f"sync partition {source_table_partition_id}, partition by {partition_by}")

    target_files_pattern = self.get_target_files_pattern(table_spec, pseudo_partition_id)
    # delete destination gcs folder before run export
    self.gcs.delete_objects_in_folder(target_files_pattern)
    self.run_export_bq_to_gcs(source_table, table_spec, partition_id, target_files_pattern, force_sync_full_table=False)

    if use_hive_partitioning:
      self.spark.truncate_hive_partition(target_table, partition_by="dt", iso_partition_id=iso_partition_id)
      self.spark.load(target_files_pattern, target_table, table_spec, use_hive_partitioning, create_table_if_not_exist=True)
    else:
      # use table_spec
      # process as hidden partitioning
      if table_spec.get('enable_insert_override',False) == True:
        self.spark.load(target_files_pattern, target_table, table_spec, use_hive_partitioning, create_table_if_not_exist=True, enable_insert_override=True)
      else:
        self.spark.truncate_hidden_partition(target_table, table_spec, partition_id=pseudo_partition_id)
        self.spark.load(target_files_pattern, target_table, table_spec, use_hive_partitioning, create_table_if_not_exist=True, enable_insert_override=False)

    self.log.info("-" * 100)
    self.log.info("synchronized:")
    self.log.info(f"-> source: {source_table}")
    self.log.info(f"-> target: {target_table}")
    self.log.info(f"-> partition: {pseudo_partition_id}")

  # sync range partitions
  def sync_partitioned_table_from_bigquery_by_range(self, source_table, table_spec, target_table, from_partition, to_partition, use_hive_partitioning=False):
    self.log.info(f"start syncing {source_table} from BQ to {target_table} for partition from {from_partition} to {to_partition} using hive partition = {use_hive_partitioning}")
    partitions = self.bq.get_table_partitions(source_table, from_partition, to_partition)
    self.log.info(f"found total {partitions.total_rows} partitions need to be sync")
    for partition in partitions:
      partition_id = partition["partition_id"]
      self.sync_partitioned_table_from_bigquery(source_table, table_spec, target_table, partition_id, use_hive_partitioning=use_hive_partitioning)

    self.log.info("=" * 100)
    self.log.info(f"sync table {source_table} done!")

  # sync generic by date, to be called by automation sync controller
  def sync_table_from_bigquery(self, source_table, target_table=None, date=None, use_hive_partitioning=False, enable_insert_override=False):
    table_spec = self.analyze_table_spec(source_table)
    # target_table = self.get_datalake_table_from_bq_fqn(source_table)
    target_table = target_table if target_table else table_spec["fqn_iceberg_table"]
    meta_type = table_spec["meta"]["type"]

    self.log.info(f"migrating:")
    self.log.info(f"-> source: {source_table}")
    self.log.info(f"-> sink: {target_table}")
    self.log.info(f"-> config: date={date}, use_hive_partitioning={use_hive_partitioning} and enable_insert_override={enable_insert_override}")
    self.log.info("-" * 100)

    if date and not self.is_valid_date_for_meta_type(meta_type, date):
      self.log.error(f"date value {date} is not compilance with meta type {meta_type}")
      return

    kind = table_spec["kind"]
    table_spec['enable_insert_override'] = False

    match kind:
      case "normal-table":
        self.sync_normal_table_from_bigquery(source_table, table_spec, target_table, date)
      case "sharded-table":
        shard = date if date else table_spec["meta"]["shard"]
        self.sync_sharded_table_from_bigquery(source_table, table_spec, target_table, shard)
      case "partitioned-table":
        if use_hive_partitioning and enable_insert_override:
          self.log.warning("Can not enable insert_override mode with hive_partitioning format. Ignore insert_override config")
          enable_insert_override = False

        table_spec['enable_insert_override'] = enable_insert_override

        if not date:
          self.log.error(f"you must specific a partition id for partitioned table, exiting...")
          return
        # TODO: if partition is hour, should be run on partition with hour pattern
        partition_id = date
        self.sync_partitioned_table_from_bigquery(source_table, table_spec, target_table, partition_id=partition_id, use_hive_partitioning=use_hive_partitioning)

  # sync generic by range, to be called by sync cli
  def sync_table_from_bigquery_by_range(self, source_table, target_table, from_date=None, to_date=None, use_hive_partitioning=False, enable_insert_override=False):

    self.log.info("*" * 100)
    self.log.info(f"migrate range:")
    self.log.info(f"-> source: {source_table}")
    self.log.info(f"-> from {from_date} to {to_date}")
    self.log.info("*" * 100)

    dates = self.generate_series(from_date, to_date)
    for date in dates:
      self.log.info("=" * 100)
      self.log.info(f"start syncing for: date={date}")
      if source_table.endswith("_*"):
        # sync for sharded table
        source_table_with_sharded = source_table.replace('*', date)
        self.sync_table_from_bigquery(source_table_with_sharded, target_table, date=date, use_hive_partitioning=use_hive_partitioning, enable_insert_override=enable_insert_override)
      else:
        # sync as normal
        self.sync_table_from_bigquery(source_table, target_table, date=date, use_hive_partitioning=use_hive_partitioning, enable_insert_override=enable_insert_override)

@click.group(name='migrate')
def migration_tools():
  """Data Lake related operation commands"""
  pass

@migration_tools.command(name='sync-one', help='sync table from Big Query')
@click.option('--source', prompt='Source table from BQ', help='Source table from BQ')
@click.option('--target', default=None, help='Destination iceberg table in Datalake')
@click.option('--date', default=None, help='Hidden partitioning partition specification (yyyyMMdd)')
@click.option('--use_hive_partitioning', is_flag=True, show_default=False, default=False, help='Hive partitioning partition specification')
@click.option('--enable_insert_override', is_flag=True, show_default=False, default=False, help='Enable this flag to avoid shuffle data writing to Iceberg. Only support for partitioned table with hidden partition')
def sync_table_from_bigquery_cli(source, target, date, use_hive_partitioning, enable_insert_override):
  migration = Migration()
  migration.sync_table_from_bigquery(source, target, date, use_hive_partitioning, enable_insert_override)

@migration_tools.command(name='sync-range', help='sync multiple partitions')
@click.option('--source', prompt='Source table from BQ', help='Source table from BQ')
@click.option('--target', default=None, help='Destination iceberg table in Datalake')
@click.option('--from_partition', default=None, help='Hidden partitioning partition specification')
@click.option('--to_partition', default=None, help='Hidden partitioning partition specification')
@click.option('--use_hive_partitioning', is_flag=True, show_default=False, default=False, help='Hive partitioning partition specification')
@click.option('--enable_insert_override', is_flag=True, show_default=False, default=False, help='Enable this flag to avoid shuffle data writing to Iceberg. Only support for partitioned table with hidden partition')
def sync_partitions_from_bigquery_cli(source, target, from_partition, to_partition, use_hive_partitioning, enable_insert_override):
  migration = Migration()
  migration.sync_table_from_bigquery_by_range(source, target, from_partition, to_partition, use_hive_partitioning, enable_insert_override)

@migration_tools.command(name='force-sync', help='force sync partitions as normal table')
@click.option('--source', prompt='Source table from BQ', help='Source table from BQ')
@click.option('--target', default=None, help='Destination iceberg table in Datalake')
def force_sync_partitions_as_normal_from_bigquery_cli(source, target):
  migration = Migration()
  migration.force_sync_partitions_as_normal_table(source, target)

if __name__ == '__main__':
  migration_tools()