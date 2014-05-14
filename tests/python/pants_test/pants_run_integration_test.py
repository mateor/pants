# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)


import optparse
import os
import unittest

from contextlib import contextmanager
from tempfile import mkdtemp
from textwrap import dedent

from twitter.common.dirutil import Lock, safe_open, safe_rmtree

from pants.base.config import Config
from pants.base.build_environment import get_buildroot
from pants.commands.goal import Goal
from pants.goal.initialize_reporting import initial_reporting
from pants.goal.run_tracker import RunTracker
from pants.tasks.nailgun_task import NailgunTask

from mock import patch


class PantsRunIntegrationTest(unittest.TestCase):
  """A baseclass useful for integration tests for targets in the same repo"""

  PANTS_SUCCESS_CODE = 0

  @classmethod
  def setUp(self):
    self.parser = optparse.OptionParser(add_help_option=False)
    self.config = Config.load()
    self.run_tracker = RunTracker.from_config(self.config)
    self.pants_workdir = mkdtemp(suffix='PANTS_WORK_DIR')
    ini = dedent('''
          [DEFAULT]
          pants_workdir:  %(workdir)s
          ''' % dict(workdir=self.pants_workdir))

    with safe_open(os.path.join(self.pants_workdir, 'pants.ini'), mode='w') as fp:
      fp.write(ini)
    self.runfile = os.path.join(self.pants_workdir, '.pants.run')

  @contextmanager
  def run_pants(self, command_args=None):
    with patch.dict('os.environ', {'PANTS_CONFIG_OVERRIDE': os.path.join(self.pants_workdir,
                                                                         'pants.ini')}):
      report = initial_reporting(self.config, self.run_tracker)
      self.run_tracker.start(report)
      self.command = Goal(self.run_tracker,
                     get_buildroot(),
                     self.parser,
                     command_args)
      try:
        self.lock = Lock.acquire(self.runfile)
        result = self.command.run(self.lock)
        yield result
      finally:
        self.lock.release()
        self.run_tracker.end()

  @classmethod
  def tearDown(self):
    NailgunTask._DAEMON_OPTION_PRESENT = False
    safe_rmtree(self.pants_workdir)
