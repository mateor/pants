# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from contextlib import contextmanager
import os
import textwrap
import unittest2 as unittest

from pants.util.contextutil import temporary_file

from pants.backend.android.tasks.sign_apk import SignApkTask


class SignApkTest(unittest.TestCase):
  """Test the package translation methods in pants.backend.android.aapt_gen."""

  _DEFAULT_KEYSTORE = '%(homedir)s/.pants.d/android/keystore_config.ini'

  @contextmanager
  def config_file(self):
    with temporary_file() as fp:
      fp.write(textwrap.dedent(
        """
        [{0}]

        keystore_config_location: {1}
        """).format(SignApkTask._CONFIG_SECTION, self._DEFAULT_KEYSTORE))
      path = fp.name
      fp.close()
      yield path