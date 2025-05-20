import logging

from typing import TYPE_CHECKING, Any
from pyhive.hive import connect

from airflow.hooks.base_hook import BaseHook
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

if TYPE_CHECKING:
  from airflow.utils.context import Context

log = logging.getLogger(__name__)

class KyuubiSparkSqlHook(BaseHook):

  def __init__(self,
      spark_conn_id='spark_sql_default',
      verbose=True
    ):

    self.spark_conn_id = spark_conn_id
    self._conn = self.get_connection(spark_conn_id)
    self._verbose = verbose

  def get_conn(self):
    """
    Establish a connection to the Kyuubi server.
    :return: A PyHive connection object
    """
    conn = self.get_connection(self.spark_conn_id)
    
    host = conn.host
    port = conn.port or 10009

    # Log connection details (avoid logging sensitive info)
    self.log.info(f"Connecting to Kyuubi at {host}:{port}")

    # Establish the PyHive connection
    return connect(host=host, port=port)

  def kill(self):
    pass
    

class SparkSQLExecuteQueryOperator(BaseOperator):

  template_fields = ["sql"]
  template_ext = [".sql"]

  @apply_defaults
  def __init__(self,
    sql,
    conf=None,
    spark_conn_id='spark_sql_default',
    *args,
    **kwargs
  ):
    
    super(SparkSQLExecuteQueryOperator, self).__init__(*args, **kwargs)

    self.spark_conn_id = spark_conn_id
    self.sql = sql
    self.conf = self.__parse_spark_sql_conf(conf)

  def execute(self, context):
    """
    Call the KyuubiSparkSqlHook to run the provided sql query
    """
    self._hook = KyuubiSparkSqlHook(
      spark_conn_id=self.spark_conn_id
    )

    conn = self._hook.get_conn()

    with conn.cursor() as cursor:
      for c in self.conf:
        self.log.info(c)
        cursor.execute(c)
      cursor.execute(self.sql)
      results = cursor.fetchone()

      self.log.info(f"Query execution completed. Results: {results}")
      return results
    
  def __parse_spark_sql_conf(self, conf):
    if isinstance(conf, str):
      return [conf]
    return conf

        