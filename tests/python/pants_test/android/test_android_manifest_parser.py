# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import textwrap
import os
import unittest
from contextlib import contextmanager

from pants.util.contextutil import temporary_file

from pants.backend.android.android_manifest_parser import AndroidManifestParser


class TestAndroidManifestParser(unittest.TestCase):
  """Test the AndroidManifestParser class."""

  @contextmanager
  def android_manifest(self,
                       manifest_element='manifest',
                       package_attribute='package',
                       uses_sdk_element='uses-sdk',
                       android_attribute='android:targetSdkVersion',
                       activity_element='activity'):
    """Represent an AndroidManifest.xml."""
    with temporary_file() as fp:
      fp.write(textwrap.dedent(
        """<?xml version="1.0" encoding="utf-8"?>
        <{manifest} xmlns:android="http://schemas.android.com/apk/res/android"
            {package}="com.pants.examples.hello" >
            <{uses_sdk}
                {android}="19" />
            <application >
                <{activity}
                    android:name="com.pants.examples.hello.HelloWorld" >
                </{activity}>
            </application>
        </{manifest}>""".format(manifest = manifest_element, package = package_attribute,
                                uses_sdk = uses_sdk_element, android = android_attribute,
                                activity = activity_element)))
      fp.close()
      path = fp.name
      yield path

  def test_get_package_name(self):
      with self.android_manifest() as manifest:
        self.assertEqual(AndroidManifestParser.get_package_name(manifest),
                         'com.pants.examples.hello')

  def test_missing_manifest_element(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.android_manifest(manifest_element='grape_soda') as manifest:
        self.assertEqual(AndroidManifestParser.get_package_name(manifest),
                         'com.pants.examples.hello')

  def test_missing_package_attribute(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.android_manifest(package_attribute='lemonade') as manifest:
        self.assertEqual(AndroidManifestParser.get_package_name(manifest),
                         'com.pants.examples.hello')

  def test_get_target_sdk(self):
    with self.android_manifest() as manifest:
      self.assertEqual(AndroidManifestParser.get_target_sdk(manifest), '19')

  def test_no_uses_sdk_element(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.android_manifest(uses_sdk_element='bourbon') as manifest:
        self.assertEqual(AndroidManifestParser.get_target_sdk(manifest), '19')

  def test_no_uses_sdk_element(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.android_manifest(uses_sdk_element='bourbon') as manifest:
        self.assertEqual(AndroidManifestParser.get_target_sdk(manifest), '19')

  def test_no_android_element(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.android_manifest(android_attribute='bourbon') as manifest:
        self.assertEqual(AndroidManifestParser.get_target_sdk(manifest), '19')

  def test_no_target_sdk_value(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.android_manifest(android_attribute='android:tonka-truck') as manifest:
        self.assertEqual(AndroidManifestParser.get_target_sdk(manifest), '19')

  def test_get_app_name(self):
    with self.android_manifest() as manifest:
      self.assertEqual(AndroidManifestParser.get_app_name(manifest), 'HelloWorld')