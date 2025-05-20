load("@python_3_10//:defs.bzl", _py_binary = "py_binary")
load("//tools:momo.bzl", "compile_pip_requirements")

package(default_visibility = ["//visibility:public"])

compile_pip_requirements(
    name = "requirements",
    extra_args = ["--allow-unsafe"],
    py_binary = _py_binary,
    requirements_in = "requirements.in",
    requirements_txt = "requirements.txt",
)
