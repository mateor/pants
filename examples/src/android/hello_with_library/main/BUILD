# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='hello_with_library',
  sources=rglobs('src/*.java'),
  manifest='AndroidManifest.xml',
  dependencies = [
    'examples/src/android/example_library',
    ':resources',
    ':support-classes',
    ':support-unpacked',
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)

unpacked_jars(name='support-unpacked',
  libraries=[':support-classes'],
  include_patterns=[
    'android/**/*.class',
  ],
)

jar_library(name='support-classes',
  jars=[
    jar(org='android.support', name='support-v4', rev='6000',
        url='file:///Users/mateor/development/pants/examples/src/android/hello_with_library/main/libs/classes.jar',),
  ],
)

jar_library(name='android-support-v4',
  jars = [
    jar(org='com.android.support', name='support-v4', rev='22.0.0'),
  ],
)
