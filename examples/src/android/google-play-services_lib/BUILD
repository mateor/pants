# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_library(
  name='google-play-services_lib',
  sources=rglobs('src/android/*java'),
  manifest='AndroidManifest.xml',
  dependencies = [
    ':resources',
    ':google-play-services'
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)


jar_library(name='google-play-services',
  jars = [
    jar(org='com.google.android', name='gms', rev='6.5.87000',
        url='file:///Users/mateor/development/pants/examples/src/android/google-play-services_lib/libs/google-play-services.jar',),
    ],
)
