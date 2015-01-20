# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import textwrap
from contextlib import contextmanager
import unittest2 as unittest

from pants.backend.android.keystore.keystore_resolver import KeystoreResolver
from pants.base.config import Config, ChainedConfig
from pants.util.contextutil import temporary_file

class TestKeystoreResolver(unittest.TestCase):

  @contextmanager
  def good_config(self):

    with temporary_file() as android_config:
      android_config.write(textwrap.dedent(
        """
      [default-debug]

      build_type: debug
      keystore_location: %(homedir)s/.android/debug.keystore
      keystore_alias: androiddebugkey
      keystore_password: android
      key_password: android
        """))
      android_config.close()
      yield android_config

  def setUp(self):
    with self.good_config() as config:
      with temporary_file() as pantsini:
        pantsini.write(textwrap.dedent(
          """
        [android-keystore-location]
        keystore_config_location: {0}
          """.format(config)))
        pantsini.close()
        self.config = Config.load(configpaths=[pantsini.name])


  def test_resolve(self):
    with self.good_config() as config:
      KeystoreResolver.resolve(config)


# TESTS
#    That android config file overrrides pants.ini
#    That the KeyResolver can raise the proper exceptions for bad data.

# I need a contextmanager that can tak arguments for sections.