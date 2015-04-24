# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='alarm',
  sources=rglobs('src/main/java/**/*java'),
  manifest='src/main/AndroidManifest.xml',
  dependencies = [
    ':gms-library',
    ':resources',
    ':appcompat',
  ],
)

android_resources(
  name='resources',
  manifest='src/main/AndroidManifest.xml',
  resource_dir='src/main/res'
)

android_library(
  name='gms-library',
  libraries=['3rdparty/android:google-play-services'],
  include_patterns=[
    '**/*.class',
  ],
)

android_library(
  name='appcompat',
  libraries=['3rdparty/android:appcompat-v7'],
  include_patterns=[
    '**/*.class',
  ],
)