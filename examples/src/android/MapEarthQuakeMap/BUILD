# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='map-quaker',
  sources=rglobs('src/course/examples/maps/earthquakemap/*java'),
  manifest='AndroidManifest.xml',
  dependencies=[
    ':resources',
    ':gms_library',
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)

android_library(
  name='gms_library',
  libraries=['3rdparty/android:google-play-services'],
  include_patterns=[
    '**/*.class',
  ],
)
