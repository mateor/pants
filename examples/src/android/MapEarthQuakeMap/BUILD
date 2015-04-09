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
    ':support-classes',
    ':gms_lib',
    ':gms_classes',
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)

unpacked_jars(name='play-services',
  libraries=[':gms_classes'],
  include_patterns=[
    'com/google/**/*.class',
  ],
)

unpacked_jars(name='support-unpacked',
  libraries=[':support-classes'],
  include_patterns=[
    '**/*.class',
  ],
)

android_library(
  name='gms_lib',
  manifest='libs/AndroidManifest.xml',
  dependencies=[
    ':google-play-services',
    ':gms_resources',
  ],
)

jar_library(name='support-classes',
  jars=[
    jar(org='android.support', name='support-v4', rev='6000',
        url='file:///Users/mateor/development/pants/examples/src/android/MapEarthQuakeMap/libs/classes.jar',),
  ],
)

jar_library(name='gms_classes',
  jars=[
    jar(org='android.gms', name='gms-classes', rev='6500',
        url='file:///Users/mateor/development/pants/examples/src/android/MapEarthQuakeMap/libs/gms/classes.jar',),
  ],
)

android_resources(
  name='gms_resources',
  manifest='libs/AndroidManifest.xml',
  resource_dir='libs/res'
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
