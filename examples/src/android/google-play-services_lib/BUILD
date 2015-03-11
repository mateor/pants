# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_library(
  name='google-play-services_lib',
  sources=rglobs('src/android/*java'),
  manifest='AndroidManifest.xml',
  dependencies=[
    ':resources',
    ':play-services',
    ':google-play-services'
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

jar_library(name='google-play-services',
  jars=[
    jar(org='com.google.android', name='gms', rev='6.5.87000',
        url='file:///Users/mateor/development/pants/examples/src/android/google-play-services_lib/libs/google-play-services.jar',),
  ],
)
