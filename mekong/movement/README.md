# Must Read
- **UserWarning:** Your application has authenticated using end user credentials from Google Cloud SDK
- Any command execute follow below instruction will directly run on production environment

# Guidelines

## Setup python environment
To run CLI on your PC, a conda environment need to be setup as required by `py_runtime`

```
py_runtime(
    name = "develop",
    interpreter_path = "/home/vinhdang/.conda/envs/develop/bin/python",
)
```

1. Create new develop env
    ```
    conda create -n develop python=3.10
    ```
2. Active your develop conda environment
    ```
    conda actiavte develop
    ```
3. Install required packages
    ```
    pip install -r $MOMO_BASE_PATH/mekong/requirements.txt
    ```

## Setup local CLI

From your momo's gerrit base folder (eg: /home/vinhdang/workspaces/mm/momo):

1. Export momo's gerrit base folder
    ```
    export MOMO_BASE_PATH=`pwd`
    ```
2. Symlink mekong/movement/scripts/datalake.sh to your shell environment
    ```
    sudo ln -s $MOMO_BASE_PATH/mekong/movement/scripts/datalake.sh /usr/local/bin/bigbang
    ```
3. Test if cli is runing as expected
    ```
    bigbang --help
    ```

    Output should be like:

    ```
    Analyzing: target //mekong/movement/python/apps:main_binary (0 packages loaded, 0 targets configured)
    [0 / 1] [Prepa] BazelWorkspaceStatusAction stable-status.txt
    [2024-05-14 15:08:15,841] INFO - USE `default`
    Usage: main.py [OPTIONS] COMMAND [ARGS]...

      Movement Utils

    Options:
      --help  Show this message and exit.

    Commands:
      bq       Bigquery related commands
      migrate  Data Lake related operation commands
      spark    Apache Spark related commands
    ```

## Migration Tools

### Setup
1. Set env for storing migration data exported from Big Query
```
export MIGRATION_DATA_GCS_LOCATION=gs://momovn-datalake-movement-us-central1-prod/gcp/bigquery
```
2. Forward spark thrift port to run spark sql
```
kubectl -n kyuubi port-forward kyuubi-0 10009:10009
```
3. All dataset must be created manual in location with patten: gs://{bucket_name}/{dataset_name}

Bucket name mapping for each catalog:
- sandbox: momovn-datalake-sandbox-us-central1-prod
- analytics: momovn-datalake-analytics-us-central1-prod
- migration: momovn-datalake-snapshots-us-central1-prod

Spark:
```
create database sandbox.backend location 'gs://momovn-datalake-sandbox-us-central1-prod/backend';
```

Trino:
```
create database analytics.backend location 'gs://momovn-datalake-analytics-us-central1-prod/backend';
```

### Migrate CLI

#### Non-partitioned table
1. Don't care gcs export `dt` location
    ```
    bigbang migrate non-partitioned-table --source=momovn-prod.APP_PERFORMANCE_REPORT.success_api --dest=sandbox.experiment.success_api
    ```
2. Explicit export to a gcs `dt` location
    ```
    bigbang migrate non-partitioned-table --source=momovn-prod.APP_PERFORMANCE_REPORT.success_api --dest=sandbox.experiment.success_api --date=20240512
    ```

#### Partitioned table
1. Export a range of partitions from BQ table to Datalake
    ```
    bigbang migrate partitions --source=momovn-dev.VINHDP.BATCH_VALIDATION_DAY --dest=sandbox.experiment.BATCH_VALIDATION_DAY --from_partition=20230101 --to_partition=20241201
    ```
2. Export only one partition from BQ table to Datalake
    ```
    bigbang migrate partition --source=momovn-dev.VINHDP.BATCH_VALIDATION_DAY --dest=sandbox.experiment.BATCH_VALIDATION_DAY --partition_id=20230815
    ```

### Example

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__phonebook_summary_stat
- Kind: normal
- Range: full
  ```
  bigbang migrate sync-one --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__phonebook_summary_stat"
  ```

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v2_vs_v3_stat
- Kind: normal
- Range: full
  ```
  bigbang migrate sync-one --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v2_vs_v3_stat"
  ```
- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__helios__phonebook
- Kind: partitioned
- Range: full
  ```
  bigbang migrate sync-range --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__helios__phonebook" --target=migration.data_collection_daily_phonebook_dashboard_in.momovn_prod__helios__phonebook --from_partition=20240101 --to_partition=20240401
  ```

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__fusion__phone_books_v2_snapshot_
- Kind: sharded
- Range: full
  ```
  bigbang migrate sync-range --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__fusion__phone_books_v2_snapshot_*" --target=migration.data_collection_daily_phonebook_dashboard_in.momovn_prod__fusion__phone_books_v2_snapshot --from_partition=20240609 --to_partition=20240610
  ```

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.mmv2__data_funcs__agent_ref_correctness_
- Kind: sharded
- Range: full
  ```
  bigbang migrate sync-range --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.mmv2__data_funcs__agent_ref_correctness_*" --target=migration.data_collection_daily_phonebook_dashboard_in.mmv2__data_funcs__agent_ref_correctness --from_partition=20240609 --to_partition=20240610
  ```

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v3_phonebook_
- Kind: sharded
- Range: full
  ```
  bigbang migrate sync-range --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v3_phonebook_*" --target=migration.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v3_phonebook --from_partition=20240609 --to_partition=20240610
  ```

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_out.momovn_prod__linker__v2_vs_v3_stat
- Kind: normal
- Range: full
  ```
  bigbang migrate sync-one --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_out.momovn_prod__linker__v2_vs_v3_stat"
  ```

- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_out.momovn_prod__linker__phonebook_summary_stat
- Kind: normal
- Range: full
  ```
  bigbang migrate sync-one --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_out.momovn_prod__linker__phonebook_summary_stat"
  ```


- Table: data-platform-exp-322803.data_collection_daily_phonebook_dashboard_out.momovn_prod__linker__v3_phonebook_
- Kind: sharded
- Range: full
  ```
  bigbang migrate sync-range --source="data-platform-exp-322803.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v3_phonebook_*" --target=migration.data_collection_daily_phonebook_dashboard_in.momovn_prod__linker__v3_phonebook --date=20240608
  ```