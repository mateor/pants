# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.backend.android.android_manifest_parser import AndroidManifestParser
from pants_test.util.test_xml_parser import TestXmlBase


class TestAndroidManifestParser(TestXmlBase):
  """Test the AndroidManifestParser class."""

  # Test AndroidManifestParser.get_package_name.
  def test_package_name(self):
    with self.xml_file() as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.package_name,
                       'com.pants.examples.hello')

  def test_missing_manifest_element(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.xml_file(manifest_element='grape_soda') as manifest:
        parsed = AndroidManifestParser.parse_manifest(manifest)
        self.assertEqual(parsed.package_name,
                         'com.pants.examples.hello')

  def test_missing_package_attribute(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.xml_file(package_attribute='bad_value') as manifest:
        parsed = AndroidManifestParser.parse_manifest(manifest)
        self.assertEqual(parsed.package_name,
                         'com.pants.examples.hello')

  def test_weird_package_name(self):
    # Should accept unexpected package names, the info gets verified in classes that consume it.
    with self.xml_file(package_value='cola') as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.package_name, 'cola')

  # Test AndroidManifestParser.target_sdk.
  def test_target_sdk(self):
    with self.xml_file() as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.target_sdk, '19')

  def test_no_uses_sdk_element(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.xml_file(uses_sdk_element='something-random') as manifest:
        parsed = AndroidManifestParser.parse_manifest(manifest)
        self.assertEqual(parsed.target_sdk, '19')

  def test_no_target_sdk_value(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.xml_file(android_attribute='android:bad_value') as manifest:
        parsed = AndroidManifestParser.parse_manifest(manifest)
        self.assertEqual(parsed.target_sdk, '19')

  def test_no_android_part(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.xml_file(android_attribute='unrelated:targetSdkVersion') as manifest:
        parsed = AndroidManifestParser.parse_manifest(manifest)
        self.assertEqual(parsed.target_sdk, '19')

  def test_missing_whole_targetsdk(self):
    with self.assertRaises(AndroidManifestParser.BadManifestError):
      with self.xml_file(android_attribute='unrelated:cola') as manifest:
        parsed = AndroidManifestParser.parse_manifest(manifest)
        self.assertEqual(parsed.target_sdk, '19')

  # Test AndroidManifestParser.application_name.
  def test_application_name(self):
    with self.xml_file() as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.application_name, 'HelloWorld')

  def test_get_weird_app_name(self):
    with self.xml_file(application_name_value='no_periods') as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.application_name, 'no_periods')

  # These last tests show AndroidManifestParser.application_name fails silently and returns None.
  def test_no_activity_element(self):
    with self.xml_file(activity_element='root_beer') as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.application_name, None)

  def test_no_android_name_attribute(self):
    with self.xml_file(android_name_attribute='android:grape') as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.application_name, None)

  def test_no_attribute_tag_match(self):
    # With attribute:value, the attribute must be declared. We declare unrelated on ln 3 of the xml.
    with self.xml_file(android_name_attribute='unrelated:match') as manifest:
      parsed = AndroidManifestParser.parse_manifest(manifest)
      self.assertEqual(parsed.application_name, None)
