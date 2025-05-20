# https://github.com/googleapis/python-pubsub/blob/main/samples/snippets/subscriber.py

import os
import logging

import json
import requests

from requests.auth import HTTPBasicAuth

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.protobuf.json_format import Parse

from mekong.movement.python.singleton_meta import SingletonMeta

logger = logging.getLogger(__name__)

class Consumer(metaclass=SingletonMeta):

  CHANGE_DATA_CAPTURE_PROJECT_ID = os.getenv("CHANGE_DATA_CAPTURE_PROJECT_ID", "data-platform-exp-322803")
  CHANGE_DATA_CAPTURE_TOPIC = os.getenv("CHANGE_DATA_CAPTURE_TOPIC", "movement-change-data-capture-dev")
  CHANGE_DATA_CAPTURE_SUBSCRIPTION_ID = os.getenv("CHANGE_DATA_CAPTURE_SUBSCRIPTION_ID", "movement-change-data-capture-subscriber")
  CHANGE_DATA_CAPTURE_SUBSCRIPTION_TIMEOUT = os.getenv("CHANGE_DATA_CAPTURE_SUBSCRIPTION_TIMEOUT", None)

  TRIGGER_DATA_SYNC_CONTROLLER_HOST = os.getenv("TRIGGER_DATA_SYNC_CONTROLLER_HOST", "http://airflow-webserver.mekong.svc.cluster.local:8080")
  TRIGGER_DATA_SYNC_CONTROLLER_ENDPOINT = os.getenv("TRIGGER_DATA_SYNC_CONTROLLER_ENDPOINT", "api/v1/datasets/events")
  TRIGGER_DATA_SYNC_CONTROLLER_USERNAME = os.getenv("TRIGGER_DATA_SYNC_CONTROLLER_USERNAME", "admin")
  TRIGGER_DATA_SYNC_CONTROLLER_PASSWORD = os.getenv("TRIGGER_DATA_SYNC_CONTROLLER_PASSWORD", "admin")
  TRIGGER_DATA_SYNC_CONTROLLER_DATASET = os.getenv("TRIGGER_DATA_SYNC_CONTROLLER_DATASET", "bigquery://datalake/movement/datasync")

  def __init__(self):
    self.subscriber = pubsub_v1.SubscriberClient()
    self.topic = self.CHANGE_DATA_CAPTURE_TOPIC
    self.subscription_id = self.subscriber.subscription_path(self.CHANGE_DATA_CAPTURE_PROJECT_ID, self.CHANGE_DATA_CAPTURE_SUBSCRIPTION_ID)
    self.timeout = None if self.CHANGE_DATA_CAPTURE_SUBSCRIPTION_TIMEOUT is None else int(self.CHANGE_DATA_CAPTURE_SUBSCRIPTION_TIMEOUT)

  def trigger_data_sync(self, projectId, jobId, trigger_data):
    
    tableProjectId = trigger_data["extra"]["projectId"]
    datasetId = trigger_data["extra"]["datasetId"]
    tableId = trigger_data["extra"]["tableId"]
    fqnTableName = f"{tableProjectId}.{datasetId}.{tableId}"
    
    try:
      url = f"{self.TRIGGER_DATA_SYNC_CONTROLLER_HOST}/{self.TRIGGER_DATA_SYNC_CONTROLLER_ENDPOINT}"
      resp = requests.post(url, json=trigger_data, auth=HTTPBasicAuth(self.TRIGGER_DATA_SYNC_CONTROLLER_USERNAME, self.TRIGGER_DATA_SYNC_CONTROLLER_PASSWORD), timeout=5)

      if resp.status_code == 200:
        respData = resp.json()
        timestamp = respData["timestamp"]

        logger.info(f'SUCCESSED: {fqnTableName} at {timestamp}')
        logger.info(f'========>: jobId: {jobId} on project id: {projectId}')
        return True
      else:
        logger.info(resp.data)
        return False
    except Exception as error:
      logger.error(f"EXCEPTION: {fqnTableName} on job id: {jobId} on project id: {projectId}")
      logger.error(error)
      return False

  def is_white_listed_resource_name(self, resourceName):
    if "/jobs/dpkc-" in resourceName:
      return False
    return True
  
  def is_white_listed_job_id(self, jobId):
    if "dlp_" in jobId or "dpkc-" in jobId:
      return False
    return True
  
  def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
    
    # TODO: parse to object with google.protobuf.json_format.Parse
    payload = json.loads(message.data.decode("utf-8"))
    resourceName = payload["protoPayload"]["resourceName"]

    if not self.is_white_listed_resource_name(resourceName):
      logger.debug(f"Resource {resourceName} is not white listed")
      message.ack()
      return

    try:
      principalEmail = payload["protoPayload"]["authenticationInfo"]["principalEmail"]
      job = payload["protoPayload"]["serviceData"]["jobCompletedEvent"]["job"]
      jobConfiguration = job["jobConfiguration"]
      projectId = job["jobName"]["projectId"]
      jobId = job["jobName"]["jobId"]

      if not self.is_white_listed_job_id(jobId):
        logger.debug(f"Job {jobId} is not white listed")
        message.ack()
        return
      
      logger.debug(f"Start processing jobId: {jobId} on projectId: {projectId}")

      match jobConfiguration:
        case {"query": query}:
          destinationTable = query["destinationTable"]
        case {"load": load}:
          destinationTable = load["destinationTable"]
        case {"extract": extract}:
          logger.debug(f"Skip job configuration for extract: {extract}")
        case {"tableCopy": tableCopy}:
          destinationTable = tableCopy["destinationTable"]
        case _:
          logger.warn(f"Unknown job configuration type for {jobConfiguration}")

      if destinationTable:
        # 2024-07-04T04:25:04.565834Z
        publish_time = payload["timestamp"]
        extra = destinationTable
        extra["publishTime"] = publish_time

        logger.debug(f"Found destination table: {destinationTable} changed by principalEmail {principalEmail} by jobId {jobId} at {publish_time}")

        trigger_data = {
          "dataset_uri": self.TRIGGER_DATA_SYNC_CONTROLLER_DATASET,
          "extra": extra
        }
        if self.trigger_data_sync(projectId, jobId, trigger_data):
          message.ack()
          return
        logger.error()
      else:
        logger.debug(f"Acked message with empty destinationTable by jobId: {jobId} on projectId: {projectId}")
        message.ack()
    except:
      # message must be sent to DLQ
      logger.error(f"Can not process log event {payload}")
      message.ack()

  def run(self):

    # https://cloud.google.com/pubsub/docs/samples/pubsub-subscriber-flow-settings#pubsub_subscriber_flow_settings-python
    # Limit the subscriber to only have ten outstanding messages at a time.
    flow_control = pubsub_v1.types.FlowControl(max_messages=5)

    streaming_pull_future = self.subscriber.subscribe(self.subscription_id, callback=self.callback, flow_control=flow_control)
    logger.info(f"Listening for messages on {self.subscription_id}..")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with self.subscriber:
      try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=self.timeout)
      except TimeoutError:
        logger.warn(f"Timeout after {self.timeout} seconds")
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.

if __name__ == '__main__':
  consumer = Consumer()
  consumer.run()
