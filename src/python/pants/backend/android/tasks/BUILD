# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


dependencies(
  name = 'common',
  dependencies = [
    'src/python/pants/backend/core/tasks:task',
    ],
  )

python_library(
  name = 'all',
  dependencies = [
    ':common',
    ':android_task',
    ],
  )

python_library(
  name = 'android',
  sources = globs('*.py'),
  dependencies = [
    pants('src/python/pants/android/distribution:distribution'),
    pants('src/python/pants/base:exceptions'),
    pants('src/python/pants/backend/core/tasks:common'),
    ]
)

python_library(
  name = 'android_task',
  sources = ['android_task.py'],
  dependencies = [
    pants(':common'),
    pants('src/python/pants/base:exceptions'),
    pants('src/python/pants/android:distribution'),
    ],
  )