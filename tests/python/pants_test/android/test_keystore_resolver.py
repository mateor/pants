# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import textwrap
from contextlib import contextmanager
import unittest2 as unittest

from pants.backend.android.keystore.keystore_resolver import KeystoreResolver
from pants.util.contextutil import temporary_file


class TestKeystoreResolver(unittest.TestCase):

  @contextmanager
  def config_file(self,
                  build_type='dekkdkdbug',
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
      self.assertEquals(os.path.isfile(config), True)
      key = KeystoreResolver.resolve(config)
      #self.assertEquals(key, 'debug', msg="hsjgdshjfghdsgfhdsgfhghsdgfhdsg")
      for k in key:
        self.assertEquals(key[k].build_type, 'debug', msg="hsjgdshjfghdsgfhdsgfhghsdgfhdsg")

        # TESTS
#    That the KeyResolver can raise the proper exceptions for bad data.

# I need a contextmanager that can tak arguments for sections.