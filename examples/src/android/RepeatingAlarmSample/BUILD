# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='alarm',
  sources=rglobs('src/main/java/**/*java'),
  manifest='src/main/AndroidManifest.xml',
  dependencies = [
    ':android-support-v4',
    ':resources',
    ':support-unpacked',
    ':support-annotations'
  ],
)

android_resources(
  name='resources',
  manifest='src/main/AndroidManifest.xml',
  resource_dir='src/main/res'
)

unpacked_jars(name='support-unpacked',
  libraries=[':android-support-v4'],
  include_patterns=[
    'android/support/**/*.class',
  ],
)

jar_library(name='support-annotations',
  jars=[
    jar(org='com.android.support', name='support-annotations', rev='22.0.0'),
  ],
)

jar_library(name='android-support-v4',
  jars = [
    jar(org='com.android.support', name='android-support-v4', rev='22.0.0'),
  ],
)