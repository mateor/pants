# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='alarm',
  sources=['src/main/java/com/example/android/repeatingalarm/RepeatingAlarmFragment.java',
           'src/main/java/com/example/android/repeatingalarm/MainActivity.java'],
  manifest='src/main/AndroidManifest.xml',
  dependencies = [
    ':resources',
    ':activities',
    ':logger',
    ':support',
  ],
)

android_resources(
  name='resources',
  manifest='src/main/AndroidManifest.xml',
  resource_dir='src/main/res'
)

# these need to be android targets to get android.jars
java_library(
  name='activities',
  sources=rglobs('src/main/java/com/example/android/common/activities/*.java'),
  dependencies = [
    ':logger',
    ':support',
  ],
)

java_library(
  name='logger',
  sources=rglobs('src/main/java/com/example/android/common/logger/*.java'),
  dependencies = [
    ':support',
  ],
)

jar_library(name='support',
  jars = [
    jar(org='android.support.v4.app', name='android-support', rev='4',
        url='file:///Users/mateor/development/pants/./examples/src/android/RepeatingAlarmSample/src/main/libs/android-support-v4.jar',),
  ],
)