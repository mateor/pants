# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='map-quaker',
  sources=rglobs('src/course/examples/maps/earthquakemap/*java'),
  manifest='AndroidManifest.xml',
  dependencies=[
    ':gms',
    ':google-play-services-new',
    ':support',
    ':resources'
    ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)

android_library(name='gms',
                sources=from_target(':play-services'),
                dependencies=[
                  ':play-services',
                  'examples/src/android/google-play-services_lib:resources',
                  ]
)

unpacked_jars(name='play-services',
              libraries=[':google-play-services-new'],
              include_patterns=[
                'com/google/**/*.class',
                ],
              )

jar_library(name='support',
  jars = [
    # wrong rev number --UPDATE
    jar(org='android.support.v4.app', name='android-support', rev='4',
        url='file:///Users/mateor/development/pants/examples/src/android/MapEarthQuakeMap/libs/android-support-v4.jar',),
  ],
)

jar_library(name='google-play-services-new',
            jars = [
              jar(org='com.google.android', name='gms', rev='6.5.87000',
                  url='file:///Users/mateor/development/pants/examples/src/android/MapEarthQuakeMap/libs/google-play-services.jar',),
              ],
            )