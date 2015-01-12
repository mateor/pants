# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

android_binary(
  name='hello',
  sources=rglobs('src/*.java'),
  manifest='AndroidManifest.xml',
  keystore_config_files=['/Users/mateor/.pants.d/android/keystore_config.ini'],
  keystores=['default-debug'],
  dependencies = [
    ':resources',
  ],
)

android_resources(
  name='resources',
  manifest='AndroidManifest.xml',
  resource_dir='res'
)
