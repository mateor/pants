# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='alarm',
  sources=rglobs('RepeatingAlarmSample/src/main/java/com/example/android/repeatingalarm/*.java'),
  manifest='RepeatingAlarmSample/src/main/AndroidManifest.xml',
  dependencies = [
    ':resources',
    ':activities',
    ':logger',
  ],
)

android_resources(
  name='resources',
  manifest='RepeatingAlarmSample/src/main/AndroidManifest.xml',
  resource_dir='RepeatingAlarmSample/src/main/res'
)

# these need to be android targets to get android.jars
java_library(
  name='activities',
  sources=rglobs('RepeatingAlarmSample/src/main/java/com/example/android/common/activities/*.java'),
)

java_library(
  name='logger',
  sources=rglobs('RepeatingAlarmSample/src/main/java/com/example/android/common/logger/*.java'),
)