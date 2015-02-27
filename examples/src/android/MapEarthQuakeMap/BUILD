# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='map-quake',
  sources=rglobs('src/course/examples/maps/earthquakemap/*java'),
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

jar_library(name='support',
            jars = [
              jar(org='android.support.v4.app', name='android-support', rev='4',
                  url='libs/android-support-v4.jar',),
              ],
            )