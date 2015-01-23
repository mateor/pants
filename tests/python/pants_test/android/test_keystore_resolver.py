# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from contextlib import contextmanager
import os
import textwrap
import unittest2 as unittest

from pants.backend.android.keystore.keystore_resolver import KeystoreResolver
from pants.util.contextutil import temporary_file

#TODO(BEFORE REVIEW) CHeck import ordering
class TestKeystoreResolver(unittest.TestCase):
  """
  Test android.keystore.key_resolver class that creates Keystore objects from .ini config files.
  """
  # This class makes use of (TODO BEFORE REVIEW) [FILL IN COMMIT NUMBER) which treats passing required options
  # empty strings get treated as None.
  @contextmanager
  def config_file(self,
                  build_type='debug',
                  keystore_location='%(homedir)s/.android/debug.keystore',
                  keystore_alias='androiddebugkey',
                  keystore_password='android',
                  key_password='android'):
    with temporary_file() as fp:
      fp.write(textwrap.dedent(
      """
      [default-debug]

      build_type: {0}
      keystore_location: {1}
      keystore_alias: {2}
      keystore_password: {3}
      key_password: {4}
      """).format(build_type, keystore_location, keystore_alias, keystore_password, key_password))
      path = fp.name
      fp.close()
      yield path

  def test_resolve(self):
    with self.config_file() as config:
      keystores = KeystoreResolver.resolve(config)
      for key in keystores:
        self.assertEquals(key.build_type, 'debug')

  def test_bad_build_type(self):
    with self.config_file(build_type="bad-build-type") as config:
      keystores = KeystoreResolver.resolve(config)
      for key in keystores:
        with self.assertRaises(ValueError):
          key.build_type

  def test_expanding_path(self):
    with self.config_file(keystore_location="~/dir") as config:
      KeystoreResolver.resolve(config)

  def test_full_path(self):
    with self.config_file(keystore_location=temporary_file) as config:
      KeystoreResolver.resolve(config)

  def test_bad_location_for_config_file(self):
    with self.assertRaises(KeystoreResolver.Error):
        KeystoreResolver.resolve(os.path.join('no', 'config_file', 'here'))

  def test_a_missing_field(self):
    with self.assertRaises(KeystoreResolver.Error):
      with self.config_file(keystore_alias="") as config:
        KeystoreResolver.resolve(config)
