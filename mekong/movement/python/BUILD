load("@trino//:python.bzl", "py_library")
load("@trino_all_deps//:requirements.bzl", "requirement")
load("//tools:momo.bzl", "pip_group")

package(default_visibility = ["//visibility:public"])

pip_group(
    name = "movement_pip_group",
    deps = [
        requirement("Flask"),
        requirement("sqlglot"),
        requirement("pydantic"),
        requirement("requests"),
        requirement("google-cloud-storage"),
        requirement("google-cloud-pubsub"),
    ],
)

py_library(
    name = "movement_lib",
    srcs = glob([
        "*.py",
    ]),
)
