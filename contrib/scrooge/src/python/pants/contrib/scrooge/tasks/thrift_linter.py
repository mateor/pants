# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.backend.jvm.tasks.jvm_tool_task_mixin import JvmToolTaskMixin
from pants.backend.jvm.tasks.nailgun_task import NailgunTask
from pants.base.exceptions import TaskError
from pants.base.workunit import WorkUnit
from pants.option.options import Options


class ThriftLintError(Exception):
  """Raised on a lint failure."""


class ThriftLinter(NailgunTask, JvmToolTaskMixin):
  """Print linter warnings for thrift files.
  """

  _CONFIG_SECTION = 'thrift-linter'

  @staticmethod
  def _is_thrift(target):
    return target.is_thrift

  @classmethod
  def register_options(cls, register):
    super(ThriftLinter, cls).register_options(register)
    register('--skip', action='store_true', help='Skip thrift linting.')
    register('--strict', default=None, action='store_true',
             help='Fail the goal if thrift linter errors are found. Overrides the '
                  '`strict-default` option.')
    register('--strict-default', default=False, advanced=True, action='store_true',
             help='Sets the default strictness for targets. The `strict` option overrides '
                  'this value if it is set.')
    register('--linter-args', default=[], advanced=True, type=Options.list,
             help='Additional options passed to the linter.')
    cls.register_jvm_tool(register, 'scrooge-linter')

  @classmethod
  def product_types(cls):
    # Declare the product of this goal. Gen depends on thrift-linter.
    return ['thrift-linter']

  @classmethod
  def prepare(cls, options, round_manager):
    super(ThriftLinter, cls).prepare(options, round_manager)
    # Linter depends on ivy running before it.
    round_manager.require_data('ivy_imports')

  @property
  def config_section(self):
    return self._CONFIG_SECTION

  @staticmethod
  def _to_bool(value):
    # Converts boolean and string values to boolean.
    return str(value) == 'True'

  def _is_strict(self, target):
    # The strict value is read from the following, in order:
    # 1. options, --[no-]strict
    # 2. java_thrift_library target in BUILD file, thrift_linter_strict = False,
    # 3. options, --[no-]strict-default
    cmdline_strict = self.get_options().strict

    if cmdline_strict is not None:
      return self._to_bool(cmdline_strict)

    if target.thrift_linter_strict is not None:
      return self._to_bool(target.thrift_linter_strict)

    return self._to_bool(self.get_options().strict_default)

  def _lint(self, target):
    self.context.log.debug('Linting {0}'.format(target.address.spec))

    classpath = self.tool_classpath('scrooge-linter')

    config_args = self.get_options().linter_args
    if not self._is_strict(target):
      config_args.append('--ignore-errors')

    paths = target.sources_relative_to_buildroot()

    args = config_args + paths

    # If runjava returns non-zero, this marks the workunit as a
    # FAILURE, and there is no way to wrap this here.
    returncode = self.runjava(classpath=classpath,
                              main='com.twitter.scrooge.linter.Main',
                              args=args,
                              workunit_labels=[WorkUnit.COMPILER])  # to let stdout/err through.

    if returncode != 0:
      raise ThriftLintError(
        'Lint errors in target {0} for {1}.'.format(target.address.spec, paths))

  def execute(self):
    if self.get_options().skip:
      return

    thrift_targets = self.context.targets(self._is_thrift)
    with self.invalidated(thrift_targets) as invalidation_check:
      errors = []
      for vt in invalidation_check.invalid_vts:
        try:
          self._lint(vt.target)
        except ThriftLintError as e:
          errors.append(str(e))
        else:
          vt.update()
      if errors:
        raise TaskError('\n'.join(errors))
