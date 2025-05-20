import os
import re
import sys
import logging

from google.cloud import storage

from mekong.movement.python.singleton_meta import SingletonMeta
from mekong.movement.python.common import CliContext

logger = logging.getLogger(__name__)

class Gcs(metaclass=SingletonMeta):

  __MIGRATION_DATA_GCS_BUCKET = "momovn-datalake-movement-us-central1-prod"

  def __init__(self):
    self.client = storage.Client()
    self.bucket_name = self.__MIGRATION_DATA_GCS_BUCKET
    self.bucket = self.client.bucket(self.bucket_name)
    self.context = CliContext()

  def get_migration_data_gcs_location(self):
    return f"gs://{self.__MIGRATION_DATA_GCS_BUCKET}/gcp/bigquery"

  def list_objects_in_folder(self, delimiter=None):
    folder = "gs://momovn-datalake-spark-files-us-central1-prod/experiment/sample/dt=2024-05-12"

    blobs = self.client.list_blobs(self.bucket_name, prefix=folder, delimiter=delimiter)

    # Note: The call returns a response only when the iterator is consumed.
    logger.info("Blobs:")
    for blob in blobs:
      logger.info(blob.name)
      return blob

    if delimiter:
      logger.info("Prefixes:")
      for prefix in blobs.prefixes:
        logger.info(prefix)
        return prefix

  @staticmethod
  def extract_bucket_name(path: str) -> str:
    pattern = r"gs:\/\/([^\/]+)\/.*"
    match = re.match(pattern, path)
    return match.group(1)

  def delete_objects_in_folder(self, prefix):
    bucket_name = self.extract_bucket_name(prefix)
    bucket = self.client.bucket(bucket_name)

    prefix = prefix.replace("/*.parquet", "").replace(f"gs://{bucket_name}/", "")
    logger.info(f"deleting objects startswith {prefix}")

    # hardcode check
    if len(prefix.split("/", 4)) < 4:
      logger.error(f"gcs prefix safety check at {prefix} can not be delete becase it is not contains at least 6 part splitted by /")
      return

    blobs_to_delete = [blob for blob in bucket.list_blobs(prefix=prefix)]
    for blob in blobs_to_delete:
      logger.debug(blob.path)
    
    if not self.context.dry_run:
      bucket.delete_blobs(blobs_to_delete)
      logger.info(f"Finished deleting objects start swith {prefix}")

if __name__ == "__main__":

  Gcs.list_objects_in_folder(
    bucket_name=sys.argv[1], prefix=sys.argv[2], delimiter=sys.argv[3]
  )