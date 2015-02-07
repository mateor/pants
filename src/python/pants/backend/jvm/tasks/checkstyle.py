# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from twitter.common.collections import OrderedSet

from pants.backend.jvm.tasks.jvm_tool_task_mixin import JvmToolTaskMixin
from pants.backend.jvm.tasks.nailgun_task import NailgunTask
from pants.base.exceptions import TaskError
from pants.base.target import Target
from pants.option.options import Options
from pants.process.xargs import Xargs
from pants.util.dirutil import safe_open


class Checkstyle(NailgunTask, JvmToolTaskMixin):

  _CHECKSTYLE_MAIN = 'com.puppycrawl.tools.checkstyle.Main'

  _CONFIG_SECTION = 'checkstyle'

  _JAVA_SOURCE_EXTENSION = '.java'

  _CHECKSTYLE_BOOTSTRAP_KEY = "checkstyle"

  @classmethod
  def register_options(cls, register):
    super(Checkstyle, cls).register_options(register)
    register('--skip', action='store_true', help='Skip checkstyle.')
    register('--configuration', help='Path to the checkstyle configuration file.')
    register('--properties', type=Options.dict, default={},
             help='Dictionary of property mappings to use for checkstyle.properties.')
    register('--confs', default=['default'],
             help='One or more ivy configurations to resolve for this target. This parameter is '
                  'not intended for general use. ')
    cls.register_jvm_tool(register, 'checkstyle')

  @classmethod
  def prepare(cls, options, round_manager):
    super(Checkstyle, cls).prepare(options, round_manager)
    round_manager.require_data('compile_classpath')

  @property
  def config_section(self):
    return self._CONFIG_SECTION

  def _is_checked(self, target):
    return (isinstance(target, Target) and
            target.has_sources(self._JAVA_SOURCE_EXTENSION) and
            (not target.is_synthetic))

  def execute(self):
    if self.get_options().skip:
      return
    targets = self.context.targets(self._is_checked)
    with self.invalidated(targets) as invalidation_check:
      invalid_targets = []
      for vt in invalidation_check.invalid_vts:
        invalid_targets.extend(vt.targets)
      sources = self.calculate_sources(invalid_targets)
      if sources:
        result = self.checkstyle(sources)
        if result != 0:
          raise TaskError('java {main} ... exited non-zero ({result})'.format(
            main=self._CHECKSTYLE_MAIN, result=result))

  def calculate_sources(self, targets):
    sources = set()
    for target in targets:
      sources.update(source for source in target.sources_relative_to_buildroot()
                     if source.endswith(self._JAVA_SOURCE_EXTENSION))
    return sources

  def checkstyle(self, sources):
    compile_classpath = self.context.products.get_data('compile_classpath')
    union_classpath = OrderedSet(self.tool_classpath('checkstyle'))
    union_classpath.update(jar for conf, jar in compile_classpath if conf in self.get_options().confs)

    args = [
      '-c', self.get_options().configuration,
      '-f', 'plain'
    ]

    if self.get_options().properties:
      properties_file = os.path.join(self.workdir, 'checkstyle.properties')
      with safe_open(properties_file, 'w') as pf:
        for k, v in self.get_options().properties.items():
          pf.write('{key}={value}\n'.format(key=k, value=v))
      args.extend(['-p', properties_file])

    # We've hit known cases of checkstyle command lines being too long for the system so we guard
    # with Xargs since checkstyle does not accept, for example, @argfile style arguments.
    def call(xargs):
      return self.runjava(classpath=union_classpath, main=self._CHECKSTYLE_MAIN,
                          args=args + xargs, workunit_name='checkstyle')
    checks = Xargs(call)

    return checks.execute(sources)
