# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import textwrap
from contextlib import contextmanager
import unittest2 as unittest

from twitter.common.collections import maybe_list

from pants.backend.android.keystore.keystore_resolver import KeystoreResolver
from pants.base.config import Config, ChainedConfig
from pants.util.contextutil import temporary_file, temporary_dir
from pants.util.dirutil import chmod_plus_x, safe_open, touch


class TestKeystoreResolver(unittest.TestCase):

  @contextmanager
  # default for testing purposes being sdk 18 and 19, with latest build-tools 19.1.0
  def distribution(self, installed_sdks=('18', '19'),
                   installed_build_tools=('19.1.0', ),
                   files='android.jar',
                   executables='aapt'):
    with temporary_dir() as sdk:
      for sdks in installed_sdks:
        touch(os.path.join(sdk, 'platforms', 'android-' + sdks, files))
      for build in installed_build_tools:
        for exe in maybe_list(executables or ()):
          path = os.path.join(sdk, 'build-tools', build, exe)
          with safe_open(path, 'w') as fp:
            fp.write('')
          chmod_plus_x(path)
      yield sdk

  @contextmanager
  def good_config(self):

    with temporary_dir() as android_config:
      path = (os.path.join(android_config, 'android_config.ini'))
      touch(path)
      with safe_open(path, 'w') as fp:
        fp.write(textwrap.dedent(
          """
        [default-debug]

        build_type: debug
        keystore_location: %(homedir)s/.android/debug.keystore
        keystore_alias: androiddebugkey
        keystore_password: android
        key_password: android
          """))
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
      config_file = os.path.join(config, 'android_config.ini')
      self.assertEquals(os.path.isfile(config_file), True)
      KeystoreResolver.resolve(config_file)
      #self.assertEquals(os.path.i)


# TESTS
#    That android config file overrrides pants.ini
#    That the KeyResolver can raise the proper exceptions for bad data.

# I need a contextmanager that can tak arguments for sections.