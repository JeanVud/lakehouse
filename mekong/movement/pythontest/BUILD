load("@trino//:python.bzl", "py_test")

py_test(
    name = "test_gcs",
    size = "small",
    srcs = ["test_gcs.py"],
    data = ["//mekong/movement/pythontest/data"],
    deps = [
        "//trino/utilities/schemautils/python:schemautils_lib",
        "//trino/utilities/schemautils/python:schemautils_pip_group_lib",
    ],
)

py_test(
    name = "test_bigquery",
    srcs = ["test_bigquery.py"],
    data = ["//mekong/movement/pythontest/data"],
    deps = [
        "//trino/utilities/schemautils/python:schemautils_lib",
        "//trino/utilities/schemautils/python:schemautils_pip_group_lib",
    ],
)

py_test(
    name = "test_spark",
    srcs = ["test_spark.py"],
    data = ["//mekong/movement/pythontest/data"],
    deps = [
        "//trino/utilities/schemautils/python:schemautils_lib",
        "//trino/utilities/schemautils/python:schemautils_pip_group_lib",
    ],
)

py_test(
    name = "test_migration",
    srcs = ["test_migration.py"],
    data = ["//mekong/movement/pythontest/data"],
    deps = [
        "//trino/utilities/schemautils/python:schemautils_lib",
        "//trino/utilities/schemautils/python:schemautils_pip_group_lib",
    ],
)
