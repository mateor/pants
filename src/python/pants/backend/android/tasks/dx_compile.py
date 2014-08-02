# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from pants.backend.android.targets.android_dex import AndroidDex
from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.tasks.android_task import AndroidTask
from pants.backend.jvm.tasks.nailgun_task import NailgunTask
from pants.base.exceptions import TaskError
from pants.base.workunit import WorkUnit
from pants.util.dirutil import safe_mkdir

class DxCompile(AndroidTask, NailgunTask):
  """
  Compile java classes into dex files, Dalvik executables.
  """
  _CONFIG_SECTION = 'dx-tool'

  # @classmethod
  # def setup_parser(cls, option_group, args, mkflag):
  #   # VM options go here dx -J<options>
  #   pass

  @classmethod
  def is_dextarget(cls, target):
    """Check if target is a candidate to have its class files compiled into dex"""
    return isinstance(target, AndroidBinary)

  def __init__(self, context, workdir):
    print("WE ARE AT DX_COMPILE")
    super(DxCompile, self).__init__(context, workdir)
    self._android_dist = self.android_sdk

  def prepare(self, round_manager):
    # gets you generated java from AaptGen in the form of synthetic
    # targets in the self.context.targets() target graph
    round_manager.require_data('java')
    # gets you a mapping from JvmTarget to the basedirs and
    # classfile paths in those basedirs generated by javac/scalac
    round_manager.require_data('classes_by_target')

  @property
  def config_section(self):
    return self._CONFIG_SECTION


  def _compile_dex(self, args):
    classpath = [self.jar_location]
    java_main = 'com.sun.tools.internal.xjc.Driver'
    return self.runjava(classpath=classpath, main=java_main, args=args, workunit_name='xjc')

  def execute(self):
    safe_mkdir(self.workdir)
    with self.context.new_workunit(name='dex_compile', labels=[WorkUnit.MULTITOOL]):  #Which code?
      for target in self.context.targets(predicate=self.is_dextarget):
        print("WE HAVE AN INTERESTING TARGET HERE!")
    #TODO check for empty class files there is no valid empty dex file.

  def dx_jar_tool(self, build_tools_version):
    """Return the appropriate dx.jar.

    :param string build_tools_version: The Android build-tools version number (e.g. '19.1.0').
    """
    dx_jar = os.path.join('build-tools', build_tools_version, 'lib', 'dx.jar')
    return self._android_dist.register_android_tool(dx_jar)