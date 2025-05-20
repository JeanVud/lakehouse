import os
import yaml

from typing import List
from pydantic import BaseModel

from mekong.movement.python.singleton_meta import SingletonMeta

class CliContext(metaclass=SingletonMeta):
  def __init__(self, log_level="INFO", dry_run=False):
    self.log_level = log_level
    self.dry_run = dry_run

class Table(BaseModel):
  name: str
  name_fqn_id: str
  origin_name_fqn: str
  schedule: str = ""
  rename_to: str
  kind: str
  enable_insert_override: bool = False
  sensor: str
  backfilling: str

class Dataset(BaseModel):
  name: str
  tables: List[Table] = []

class WhiteLists(metaclass=SingletonMeta):

  __FILE_PATH__ = os.path.dirname(os.path.realpath(__file__))
  __CONFIG_WHITELIST_TABLES = "{}/services/conf/whitelist-tables.yaml".format(__FILE_PATH__)
  __CONFIG_NOAH_DATASETS = "{}/services/conf/noah-tables.yaml".format(__FILE_PATH__)

  def __init__(self):

    self.whitelists_dict = {}
    self.noah_datasets_dict = {}
    self.datasets = []

    with open(self.__CONFIG_WHITELIST_TABLES, 'r') as file:
      self.config_whitelist_tables = yaml.safe_load(file)

    with open(self.__CONFIG_NOAH_DATASETS, 'r') as file:
      self.config_noah_datasets = yaml.safe_load(file)

    for dataset in self.config_whitelist_tables:
      dataset_name = dataset["name"]
      dataset_obj = Dataset(name=dataset_name)

      for table in dataset["tables"]:
        table_name = table["name"]
        rename_to = table["rename_to"] if "rename_to" in table else ""
        kind = table["kind"] if "kind" in table else ""
        schedule = table["schedule"] if "schedule" in table else ""
        sensor = table["sensor"] if "sensor" in table else ""
        backfilling = table["backfilling"] if "backfilling" in table else ""
        enable_insert_override = bool(table.get('enable_insert_override', False))
        fqn_table_name_lower = f"{dataset_name}.{table_name}".lower()
        origin_name_fqn = f"{dataset['name']}.{table_name}"

        table = Table(
          name=table_name,
          name_fqn_id=fqn_table_name_lower,
          origin_name_fqn=origin_name_fqn,
          rename_to=rename_to,
          kind=kind,
          schedule=schedule,
          sensor=sensor,
          backfilling=backfilling,
          enable_insert_override=enable_insert_override
        )

        dataset_obj.tables.append(table)
        self.whitelists_dict[fqn_table_name_lower] = table

      self.datasets.append(dataset_obj)

    for dataset in self.config_noah_datasets["tables"]:
      self.noah_datasets_dict[dataset] = 1


  def is_allowed(self, fqn_table):
    fqn_table_lower = fqn_table.lower()
    return fqn_table_lower in self.whitelists_dict
  
  def is_force_sync_full_table(self, fqn_table):
    table = self.whitelists_dict[fqn_table]
    
    if table.kind == "normal-table":
      return True
    
    return False
  
  def is_scheduled_table(self, fqn_table):
    table = self.whitelists_dict[fqn_table]

    if table.schedule != "":
      return True
    return False
  
  def is_noah_schema(self, fqn_table):
    schema_lower = fqn_table.split(".")[1].lower()
    return schema_lower in self.noah_datasets_dict
  
  def get_whitelist_config_for_table(self, fqn_table):
    return self.whitelists_dict[fqn_table]
  
class MigrationMapper(metaclass=SingletonMeta):
  def __init__(self):
    # Derived Prod
    # - BigQuery: momovn-prod.APP_PERFORMANCE_REPORT.SERVICE_NAME_LIST
    # - DataLake: analytics.app_performance_report.service_name_list
    # Derived Mmv2
    # - BigQuery: project-5400504384186300846.APP_PERFORMANCE_REPORT.SERVICE_NAME_LIST
    # - DataLake: sandbox_oss.app_performance_report.service_name_list
    # self.production_catalog_mapper = {
    #   "momovn-prod": "analytics",
    #   "project-5400504384186300846": "sandbox_oss"
    # }

    # Raw Prod
    # - BigQuery: momovn-prod.CALL_CENTER.AGENT_20240520
    # - DataLake: stage.call_center.agent

    # BiqQuery: momovn-data-platform.data_tracking_fs_app_performance_report_in.momovn_prod__app_performance_report__ap_32s_session_v5
    # DataLake: stage.data_tracking_fs_app_performance_report_in.momovn_prod__app_performance_report__ap_32s_session_v5
    # Note: change only catalog name
    # self.snapshot_catalog_mapper_overrides = {
    #   "momovn-data-platform": "stage"
    # }

    self.schema_mapper_overrides = {
      "momovn-data-platform.report": "stage.report_cdo"
    }

    self.table_mapper_overrides = {
      "momovn-data-platform.report.table_to_be_forced": "stage.report_cdo.overrided_table"
    }

    self.whitelists = WhiteLists()

  def get_datalake_table_from_bq_fqn(self, bq_table_fqn):
    # process higher order override
    if bq_table_fqn in self.table_mapper_overrides:
      return self.table_mapper_overrides[bq_table_fqn]
    
    schema = ".".join(bq_table_fqn.split(".")[:2])
    for origin_schema, target_schema in self.schema_mapper_overrides.items():
      if schema == origin_schema:
        return bq_table_fqn.replace(origin_schema, target_schema)

    catalog = ".".join(bq_table_fqn.split(".")[:1])
    # if catalog == "momovn-data-platform":
    #   return bq_table_fqn.replace("momovn-data-platform", catalog)

    # if not match any override, process as normal mapping
    if self.whitelists.is_noah_schema(bq_table_fqn):
      return bq_table_fqn.replace("momovn-prod", "stage.").replace("project-5400504384186300846", "raw")
    elif bq_table_fqn.startswith("momovn-prod") or bq_table_fqn.startswith("project-5400504384186300846"):
      return bq_table_fqn.replace("momovn-prod", "analytics").replace("project-5400504384186300846", "sandbox")
    elif bq_table_fqn.startswith("data-platform-exp-322803"):
      return bq_table_fqn.replace("data-platform-exp-322803", "migration")
    elif bq_table_fqn.startswith("momovn-data-platform"):
      return bq_table_fqn.replace("momovn-data-platform", "analytics")
    elif bq_table_fqn.startswith("momovn-mini-app-analyst"):
      return bq_table_fqn.replace("momovn-mini-app-analyst", "analytics")
    else:
      project = bq_table_fqn.split(".")[0].replace("-", "_")
      table = ".".join(bq_table_fqn.split(".")[1:]).replace("-", "_")
      # default to analytics.{project_id}__{schema}
      return f"analytics.{project}__{table}"

