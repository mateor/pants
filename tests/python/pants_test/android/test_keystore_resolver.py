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

  def test_expand_path(self):
    with self.config_file(keystore_location="~/dir") as config:
      KeystoreResolver.resolve(config)

  def test_full_path(self):
    #TODO (BEFORE REVIEW) if the get_required patch is merged, then use that.
    #   else define a second bad config file for further tests.
    with self.config_file(keystore_location="") as config:
      KeystoreResolver.resolve(config)

  def test_no_config_file(self):
    with self.assertRaises(KeystoreResolver.Error):
        KeystoreResolver.resolve(os.path.join('no', 'config_file', 'here'))

    # TESTS
#    That the KeyResolver can raise the proper exceptions for bad data.
