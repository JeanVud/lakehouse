load("@trino//:python.bzl", "py_binary")
load("//tools:momo.bzl", "py3_image")

py3_image(
    name = "main_deploy",
    srcs = glob([
        "*.py",
    ]),
    base = "//dockerfiles:python3_10_8_base",
    layers = [
        "//mekong/movement/python:movement_pip_group",
    ],
    main = "main.py",
    deps = [
        "//mekong/movement/python:movement_lib",
    ],
)

# bazel run --incompatible_use_python_toolchains=false --python_top=//mekong/movement/python/apps:develop //mekong/movement/python/apps:main_binary
py_runtime(
    name = "develop",
    interpreter_path = "/home/vinhdang/.conda/envs/develop/bin/python",
)

# bazel will use system python binary instead of bazel env
py_binary(
    name = "main_binary",
    srcs = ["main.py"],
    deps = [
        "//mekong/movement/python:movement_lib",
    ],
)
