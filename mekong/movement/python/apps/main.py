import os
import logging
import click
import pathlib
import typing

from flask import Flask

from mekong.movement.python.common import CliContext
from mekong.movement.python.gcs import Gcs
from mekong.movement.python.bigquery import bigquery_tools, BigQuery
from mekong.movement.python.spark import spark_tools, Spark
from mekong.movement.python.migration import migration_tools, Migration

logger = logging.getLogger(__name__)

app = Flask(__name__)
#gcs = Gcs()
#spark = Spark()
#bq = BigQuery()
#migration = Migration()

#@app.route("/api/v1/table", methods=['POST', 'GET'])
#def register():
#  gcs.list_objects_in_folder()
#  return "hello"

@click.group()
@click.option('--log-level', default="INFO")
@click.option('--dry-run/--no-dry-run', default=False)
@click.pass_context
def cli(ctx, log_level, dry_run):
  """Movement CLI Utils"""
  ctx.obj = CliContext(log_level, dry_run)

  # global settings
  logging.getLogger().setLevel(log_level)

  if dry_run:
    logger.warning("running cli command in dryrun mode, nothing executed in remote system!")
    logger.info("-" * 100)

if __name__ == '__main__':
  # app.run(host='0.0.0.0')
  # register()
  cli.add_command(bigquery_tools)
  cli.add_command(spark_tools)
  cli.add_command(migration_tools)
  cli()