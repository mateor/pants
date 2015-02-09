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
                       manifest_element='manifest'):
    """Represent an AndroidManifest.xml."""
    with temporary_file() as fp:
      fp.write(textwrap.dedent(
        """<?xml version="1.0" encoding="utf-8"?>
        <{manifest} xmlns:android="http://schemas.android.com/apk/res/android"
            package="com.pants.examples.hello" >
            <uses-sdk
                android:targetSdkVersion="19" />
            <application >
                <activity
                    android:name="com.pants.examples.hello.HelloWorld" >
                </activity>
            </application>
        </{manifest}>""".format(manifest = manifest_element)))
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