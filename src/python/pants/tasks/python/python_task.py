# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from pants.python.interpreter_cache import PythonInterpreterCache
from pants.tasks import Task, TaskError


class PythonTask(Task):
  def __init__(self, context, workdir):
    super(PythonTask, self).__init__(context, workdir)
    self.conn_timeout = self.context.options.conn_timeout

    self.interpreter_cache = PythonInterpreterCache(self.context.config,
                                                    logger=self.context.log.debug)
    interpreters = self.context.options.interpreters or [b'']
    self.interpreter_cache.setup(filters=interpreters)
    interpreters = self.interpreter_cache.select_interpreter(
      list(self.interpreter_cache.matches(interpreters)))
    if len(interpreters) != 1:
      raise TaskError('Unable to detect suitable interpreter.')
    else:
      self.context.log.debug('Selected %s' % interpreters[0])
    self._interpreter = interpreters[0]

  @property
  def interpreter(self):
    return self._interpreter
