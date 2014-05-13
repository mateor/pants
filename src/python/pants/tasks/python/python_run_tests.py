# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from pants.base.workunit import WorkUnit
from pants.python.test_builder import PythonTestBuilder
from pants.targets.python_tests import PythonTests, PythonTestSuite
from pants.tasks import TaskError
from pants.tasks.python.python_task import PythonTask


class PythonRunTests(PythonTask):
  def execute(self, targets):
    def is_python_test(target):
      # Note that we ignore PythonTestSuite, because we'll see the PythonTests targets
      # it depends on anyway,so if we don't we'll end up running the tests twice.
      # TODO(benjy): Once we're off the 'build' command we can get rid of python_test_suite,
      # or make it an alias of dependencies().
      return isinstance(target, PythonTests)

    test_targets = filter(is_python_test, targets)
    if test_targets:
      test_builder = PythonTestBuilder(test_targets, ['--color', 'yes'], '.',
                                       interpreter=self.interpreter,
                                       conn_timeout=self.conn_timeout)
      with self.context.new_workunit(name='run',
                                     labels=[WorkUnit.TOOL, WorkUnit.TEST]) as workunit:
        # pytest uses py.io.terminalwriter for output. That class detects the terminal
        # width and attempts to use all of it. However we capture and indent the console
        # output, leading to weird-looking line wraps. So we trick the detection code
        # into thinking the terminal window is narrower than it is.
        cols = os.environ.get('COLUMNS', 80)
        os.environ['COLUMNS'] = str(int(cols) - 30)
        try:
          if test_builder.run(workunit=workunit) != 0:
            raise TaskError()
        finally:
          os.environ['COLUMNS'] = cols
