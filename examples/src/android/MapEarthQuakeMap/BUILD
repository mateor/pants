# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='map-quaker',
  sources=rglobs('src/course/examples/maps/earthquakemap/*java'),
  manifest='AndroidManifest.xml',
  dependencies=[
    ':google-play-services',
    ':play-services',
    ':resources',
    ':support-unpacked',
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)

unpacked_jars(name='play-services',
  libraries=[':google-play-services'],
  include_patterns=[
    'com/google/**/*.class',
  ],
)

unpacked_jars(name='support-unpacked',
  libraries=[':android-support-v4'],
  include_patterns=[
    'android/**/*.java',
  ],
)


jar_library(name='android-support-v4',
  jars = [
    jar(org='com.android.support', name='support-v4', rev='22.0.0'),
  ],
)

jar_library(name='google-play-services',
  jars=[
    jar(org='com.google.android.gms', name='play-services', rev='6.5.87'),
  ],
)
