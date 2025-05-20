import os
import logging
import click
import re

from typing import Union

# https://cloud.google.com/python/docs/reference/bigquery/latest/summary_overview
from google.cloud import bigquery
from google.cloud.bigquery.table import RangePartitioning, TimePartitioning
from google.api_core.exceptions import NotFound

from mekong.movement.python.singleton_meta import SingletonMeta
from mekong.movement.python.common import CliContext
from mekong.movement.python.gcs import Gcs

class BigQuery(metaclass=SingletonMeta):

  def __init__(self):
    self.log = logging.getLogger(__name__)
    self.gcs = Gcs()
    self.client = bigquery.Client()
    self.context = CliContext()

  def get_partition_spec(self, table) -> Union[RangePartitioning, TimePartitioning, None]:
    try:
      bq_table = self.client.get_table(table)
    except NotFound:
      self.log.error(f"table {table} is not found")
      return None
    
    return bq_table.time_partitioning
  
  def get_sharding_spec(self, table):
    sharding_pattern = re.compile("^(.*)_([0-9]{8})$")
    m = sharding_pattern.match(table)
    if m:
      return {"is_sharded": True, "name": m.group(1), "shard": m.group(2), "type": "DAY"}
    return {"is_sharded": False, "name": table, "shard": None, "type": None}
  
  #####################################################################

  def is_partitioning_table(self, table):
    try:
      bq_table = self.client.get_table(table)
    except NotFound:
      self.log.error(f"table {table} is not found")
      return None
    
    return bq_table.partitioning_type
  
  def is_sharding_table(self, table):
    sharding_pattern = re.compile("^(.*)_([0-9]{8})$")
    m = sharding_pattern.match(table)
    if m:
      return m.group(1), m.group(2)
    return None, None

  def get_table_partitions(self, table, from_partition, to_partition):

    fqn = table.split(".")
    project = fqn[0]
    dataset = fqn[1]
    table = fqn[2]

    sql = f"""
      SELECT * FROM `{project}.{dataset}.INFORMATION_SCHEMA.PARTITIONS`
      WHERE table_name = '{table}'
        AND partition_id >= '{from_partition}'
        AND partition_id <= '{to_partition}'
    """

    rows = self.client.query_and_wait(sql)
    return rows
  
  def get_table_partitions_from_time(self, table, modified_from):
    fqn = table.split(".")
    project = fqn[0]
    dataset = fqn[1]
    table = fqn[2]

    sql = f"""
      SELECT * FROM `{project}.{dataset}.INFORMATION_SCHEMA.PARTITIONS`
      WHERE table_name = '{table}'
        AND last_modified_time >= '{modified_from}'
    """

    rows = self.client.query_and_wait(sql)
    return rows.total_rows, rows

  def get_partition_specification(self, table) -> Union[RangePartitioning, TimePartitioning, None]:
    try:
      bq_table = self.client.get_table(table)
    except NotFound:
      self.log.error(f"table {table} is not found")
      return None
    
    return bq_table.time_partitioning
      
  def run_bq_job(self, table_ref, destination_uri):
    if not self.context.dry_run:
      job_config = bigquery.job.ExtractJobConfig()
      job_config.compression = "ZSTD"
      job_config.destination_format = bigquery.DestinationFormat.PARQUET

      # delete destination gcs folder before run export
      # self.gcs.delete_objects_in_folder(destination_uri)

      # start run export job
      extract_job = self.client.extract_table(
        table_ref,
        destination_uri,
        # Location must match that of the source table.
        location="US",
        job_config=job_config,
      )  # API request
      extract_job.result()  # Waits for job to complete.

  def run_query(self, query):
    self.client.query_and_wait(query)

  def export_to_gcs(self, source_table_ref, target_files_pattern):
    self.run_bq_job(source_table_ref, target_files_pattern)
    self.log.info(f"exported:")
    self.log.info(f"-> from: {source_table_ref}")
    self.log.info(f"-> to:   {target_files_pattern}")
    self.log.info("-" * 100)
    return target_files_pattern

@click.group(name='bq')
def bigquery_tools():
  """Bigquery related commands"""
  pass

@bigquery_tools.command(name='export', help='export bigquery table to gcs')
@click.option('--table', prompt='Bigquery fully table name', help='bigquery table name')
@click.option('--partition_id', prompt='Bigquery partition id', help='bigquery partition id')
def export_to_gcs_cli(table, partition_id):
  bq = BigQuery()
  bq.export_to_gcs(table, partition_id)

if __name__ == '__main__':
  bigquery_tools()