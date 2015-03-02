# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='google-play-services-lib',
  sources=rglobs('src/android/*java'),
  manifest='AndroidManifest.xml',
  dependencies = [
    ':resources',
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)

jar_library(name='google-play-services',
  jars = [
    jar(org='com.google.android.gms', name='google-play-services', rev='4',
        url='libs/google-play-services.jar',),
  ],
)