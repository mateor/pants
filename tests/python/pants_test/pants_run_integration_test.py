# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)


import optparse
import os
import subprocess
import unittest

from contextlib import contextmanager
from tempfile import mkdtemp
from textwrap import dedent

from twitter.common.dirutil import Lock, safe_open, safe_rmtree

from mock import patch


class PantsRunIntegrationTest(unittest.TestCase):
  """A baseclass useful for integration tests for targets in the same repo"""

  PANTS_SUCCESS_CODE = 0

  @classmethod
  def setUp(self):
    self.pants_workdir = mkdtemp(suffix='PANTS_WORK_DIR')
    ini = dedent('''
          [DEFAULT]
          pants_workdir:  %(workdir)s
          ''' % dict(workdir=self.pants_workdir))

    with safe_open(os.path.join(self.pants_workdir, 'pants.ini'), mode='w') as fp:
       fp.write(ini)

  @contextmanager
  def run_pants(self, command_args=None):
    with patch.dict('os.environ', {'PANTS_CONFIG_OVERRIDE': os.path.join(self.pants_workdir,
                                                                         'pants.ini'),
                                   'PANTS_DEV': '1'}):
      pants_commands = ['./pants', 'goal'] + command_args
      result = subprocess.call(pants_commands)
      yield result

  @classmethod
  def tearDown(self):
    safe_rmtree(self.pants_workdir)
