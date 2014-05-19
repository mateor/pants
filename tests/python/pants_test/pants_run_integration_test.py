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

from twitter.common.contextutil import temporary_dir
from twitter.common.dirutil import Lock, safe_open, safe_rmtree

from mock import patch


class PantsRunIntegrationTest(unittest.TestCase):
  """A baseclass useful for integration tests for targets in the same repo"""

  PANTS_SUCCESS_CODE = 0

  @contextmanager
  def run_pants(self, command_args=None):
    with temporary_dir() as work_dir:
      print(work_dir)
      ini = dedent('''
              [DEFAULT]
              pants_workdir:  %(workdir)s
              ''' % dict(workdir=work_dir))

      ini_file_name = os.path.join(work_dir, 'pants.ini')
      with safe_open(ini_file_name, mode='w') as fp:
        fp.write(ini)
      with patch.dict('os.environ',{'PANTS_CONFIG_OVERRIDE': ini_file_name,
                                    'PANTS_DEV': '1'}):
        pants_commands = ['./pants', 'goal'] + command_args
        result = subprocess.call(pants_commands)
        yield result
