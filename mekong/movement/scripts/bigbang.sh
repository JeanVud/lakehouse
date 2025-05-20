#!/bin/bash

exec bazel run \
  --ui_event_filters=DEBUG \
  --incompatible_use_python_toolchains=false \
  --python_top=//mekong/movement/python/apps:develop \
  //mekong/movement/python/apps:main_binary \
  -- "$@"