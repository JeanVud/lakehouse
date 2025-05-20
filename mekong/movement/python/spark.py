import os
import logging
import click

from pyhive import hive

from mekong.movement.python.singleton_meta import SingletonMeta
from mekong.movement.python.common import CliContext

class Spark(metaclass=SingletonMeta):

  SPARK_SQL_HOST  = os.getenv("SPARK_SQL_HOST", "localhost")
  SPARK_SQL_PORT  = os.getenv("SPARK_SQL_PORT", "10009")

  def __init__(self):
    self.cursor = hive.connect(host=self.SPARK_SQL_HOST, port=self.SPARK_SQL_PORT).cursor()
    self.context = CliContext()
    self.log = logging.getLogger(__name__)

  def execute_then_fetchone(self, sql):
    if self.context.dry_run:
      self.log.info(f"execute query: {sql}")
      return None

    self.cursor.execute(sql)
    return self.cursor.fetchone()
  
  def generate_target_location_for_sharding_table(self, iceberg_table):
    location = "gs://momovn-not-existed-bucket/schema/table/parttition"
    try:
      database = ".".join(iceberg_table.split(".")[:2])
      table_name = iceberg_table.split(".")[2]

      self.cursor.execute(f"describe database {database};")
      results = self.cursor.fetchall()

      for row in results:
        info_name, info_value = row
        if info_name.strip() == 'Location':
          location = f"{info_value}/{table_name}"
      return location
    except:
      self.log.info(f"Table {iceberg_table} is not found!")
      return location

  def is_table_exists(self, iceberg_table):
    try:
      sql = f"select 1 from {iceberg_table} limit 0"
      self.execute_then_fetchone(sql)
      return True
    except:
      self.log.info(f"Table {iceberg_table} is not found!")
      return False

  def truncate_table(self, iceberg_table):

    if not self.is_table_exists(iceberg_table):
      return True

    try:
      sql = f"truncate table {iceberg_table}"
      self.execute_then_fetchone(sql)
      return True
    except:
      self.log.info(f"table {iceberg_table} truncated!")
      return False

  def truncate_hive_partition(self, iceberg_table, partition_by, iso_partition_id):

    if not self.is_table_exists(iceberg_table):
      return True

    try:
      sql = f"delete from {iceberg_table} where {partition_by} = '{iso_partition_id}'"
      self.execute_then_fetchone(sql)
      return True
    except:
      self.log.info(f"partition {iso_partition_id} on {iceberg_table} can not be truncated!")
      return False

  def truncate_hidden_partition(self, iceberg_table, table_spec, partition_id):

    if not self.is_table_exists(iceberg_table):
      return True

    field = table_spec["meta"]["field"]
    fmt = table_spec["meta"]["fmt"]

    try:
      # __NULL__
      if partition_id == "20000101":
        sql = f"delete from {iceberg_table} where {field} is null"
      else:
        sql = f"delete from {iceberg_table} where date_format({field}, '{fmt}') = '{partition_id}'"
      self.execute_then_fetchone(sql)
      return True
    except:
      self.log.info(f"partition {partition_id} on {iceberg_table} can not be truncated!")
      return False


  def generate_default_hive_select_statement_for_partition_cols(self, partition_by):
    selected_cols = list(map(lambda col: f"'' as {col}", partition_by.split(",")))
    return ", ".join(selected_cols)

  def is_empty_files(self, source_files):

    sql = f"select count(1) as cnt from `parquet`.`{source_files}`"
    row = self.execute_then_fetchone(sql)

    if row is None or row[0] > 0:
      return False
    return True

  def load_parquet_files_to_iceberg_table(self, source_files, iceberg_table, enable_insert_override=False):

    if not enable_insert_override:
      sql = f"""insert into {iceberg_table} select * from parquet.`{source_files}`"""
    else:
      self.log.info("Enabled insert overwrite. Config spark.sql.iceberg.distribution-mode to none and spark.sql.sources.partitionOverwriteMode to dynamic")
      self.cursor.execute("set `spark.sql.iceberg.distribution-mode`=`none`")
      self.cursor.execute("set `spark.sql.sources.partitionOverwriteMode`=`dynamic`")
      sql = f"insert overwrite {iceberg_table} select * from parquet.`{source_files}`;"

    self.log.info(f'Query: {sql}')
    result = self.execute_then_fetchone(sql)

    if result is None:
      return False

    return True

  def add_parquet_files_to_iceberg_partitioned_table(self, source_files, partition_by, iceberg_table):

    first_partition_col = partition_by.split(",")[0]
    source_files_base_path = source_files.split(first_partition_col)[0]
    partition_idx = source_files.index(first_partition_col)
    partition_filter = source_files[partition_idx:].replace("/*.parquet", "")

    def convert_partition_to_map_value(partition):
      kv = partition.split("=")
      return f"'{kv[0]}', '{kv[1]}'"

    partitions = list(map(lambda partition: convert_partition_to_map_value(partition), partition_filter.split("/")))
    partitions_map_values = ", ".join(partitions)

    catalog = iceberg_table.split(".")[0]
    self.log.info(f"loading files from {source_files_base_path} with partition_filter {partition_filter} to table {iceberg_table}")

    sql = f"""
      CALL {catalog}.system.add_files(
        table => '{iceberg_table}',
        source_table => '`parquet`.`{source_files_base_path}`',
        partition_filter => map({partitions_map_values})
      )
    """

    result = self.execute_then_fetchone(sql)

    if result is None:
      return False
    return True

  def create_table_from_parquet_schema(self, source_files, iceberg_table):

    sql = f"""
      create table {iceberg_table} using iceberg
      as
      select *
      from parquet.`{source_files}` limit 0;
    """

    result = self.execute_then_fetchone(sql)

    if result is None:
      return False
    return True

  def create_table_from_parquet_schema_using_hive_partition(self, source_files, iceberg_table, table_spec):

    partition_by = table_spec["meta"]["partition_by"]
    selected_cols = self.generate_default_hive_select_statement_for_partition_cols(partition_by)

    sql = f"""
      create table {iceberg_table} using iceberg partitioned by ({partition_by})
      as
      select *, {selected_cols}
      from parquet.`{source_files}` limit 0;
    """

    result = self.execute_then_fetchone(sql)

    if result is None:
      return False
    return True

  def create_table_from_parquet_schema_using_hidden_partition(self, source_files, iceberg_table, table_spec):

    field = table_spec["meta"]["field"]
    transform = table_spec["meta"]["type"]
    sql = f"""
      create table {iceberg_table} using iceberg partitioned by ({transform}({field}))
      as
      select *
      from parquet.`{source_files}` limit 0;
    """

    result = self.execute_then_fetchone(sql)

    if result is None:
      return False
    return True

  def create_table_if_not_exist(self, source_files, iceberg_table, table_spec, use_hive_partitioning):
    if self.is_table_exists(iceberg_table):
      self.log.info(f"found table {iceberg_table} with partition: TBD")
    else:
      if not self.context.dry_run:
        kind = table_spec["kind"]
        match kind:
          case "normal-table":
            self.create_table_from_parquet_schema(source_files, iceberg_table)
          case "sharded-table":
            self.create_table_from_parquet_schema_using_hive_partition(source_files, iceberg_table, table_spec)
          case "partitioned-table":
            if use_hive_partitioning:
              self.create_table_from_parquet_schema_using_hive_partition(source_files, iceberg_table, table_spec)
            else:
              self.create_table_from_parquet_schema_using_hidden_partition(source_files, iceberg_table, table_spec)

      self.log.info(f"table {iceberg_table} is created")

  def load(
     self,
     source_files,
     iceberg_table,
     table_spec,
     use_hive_partitioning=False,
     create_table_if_not_exist=False,
     enable_insert_override=False
  ):

    if create_table_if_not_exist:
      self.create_table_if_not_exist(source_files, iceberg_table, table_spec, use_hive_partitioning)

    # TODO: Optimization candidate - should we omitted empty file check for hidden partitioning because empty file is rare
    # this check aim to prevent empty file on iceberg table, causing can not remove them from iceberg table
    if self.is_empty_files(source_files):
      self.log.warn(f"source files {source_files} is empty, refuse to import")
      return

    self.log.info("-" * 100)
    self.log.info(f"loading:")
    self.log.info(f"-> source: {source_files}")
    self.log.info(f"-> sink: {iceberg_table}")
    self.log.info(f"-> config: create_table_if_not_exist={create_table_if_not_exist}, use_hive_partitioning={use_hive_partitioning} and enable_insert_override={enable_insert_override}")
    self.log.info("-" * 100)

    if not self.context.dry_run:
      kind = table_spec["kind"]
      match kind:
        case "normal-table":
          self.load_parquet_files_to_iceberg_table(source_files, iceberg_table, False)
        case "sharded-table":
          partition_by = table_spec["meta"]["partition_by"]
          self.add_parquet_files_to_iceberg_partitioned_table(source_files, partition_by, iceberg_table)
        case "partitioned-table":
          if use_hive_partitioning:
            # run call to load parquet files
            partition_by = table_spec["meta"]["partition_by"]
            self.add_parquet_files_to_iceberg_partitioned_table(source_files, partition_by, iceberg_table)
          else:
            # Run query to insert table
            self.load_parquet_files_to_iceberg_table(source_files, iceberg_table, enable_insert_override)


@click.group(name='spark')
def spark_tools():
  """Apache Spark related commands"""
  pass

@spark_tools.command(name='load', help='load data from gcs to iceberg table')
@click.option('--iceberg_table', prompt='Iceberg target table', help='Iceberg target table')
@click.option('--source_files', prompt='GCS source files', help='GCS files')
@click.option('--partition_by', prompt='Partition spec', help='Partition columns specification for new table')
@click.option('--use_hive_partitioning', is_flag=True, show_default=False, default=False, help='Hive partitioning partition specification')
@click.option('--enable_insert_override', is_flag=True, show_default=False, default=False, help='Enable this flag to avoid shuffle data writing to Iceberg. Only support for partitioned table with hidden partition')
def load_cli(source_files, iceberg_table, partition_by, use_hive_partitioning, enable_insert_override):
  spark = Spark()
  spark.load(source_files, iceberg_table, partition_by, use_hive_partitioning, enable_insert_override)

if __name__ == '__main__':
  spark_tools()