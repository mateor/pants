# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from twitter.common import log

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.targets.android_target import AndroidTarget
from pants.backend.android.tasks.aapt_task import AaptTask
from pants.base.workunit import WorkUnit
from pants.util.dirutil import safe_mkdir

class AaptBuilder(AaptTask):


  @classmethod
  def product_types(cls):
    return ['apk']

  @staticmethod
  def is_app(target):
    return isinstance(target, AndroidBinary)

  @staticmethod
  def is_android(target):
    return isinstance(target, AndroidTarget)

  def __init__(self, context, workdir):
    super(AaptBuilder, self).__init__(context, workdir)

  def prepare(self, round_manager):
    round_manager.require_data('java')
    round_manager.require_data('dex')

  def render_args(self, target, output_dir):
    args = []

    if self._forced_build_tools_version:
      args.append(self.aapt_tool(self._forced_build_tools_version))
    else:
      args.append(self.aapt_tool(target.build_tools_version))

    #TODO (MATEOR) update for this subclass
    # Glossary of used aapt flags. Aapt handles a ton of action, this will continue to expand.
    #   : 'package' is the main aapt operation (see class docstring for more info).
    #   : '-m' is to "make" a package directory under location '-J'.
    #   : '-J' Points to the output directory.
    #   : '-M' is the AndroidManifest.xml of the project.
    #   : '-S' points to the resource_dir to "spider" down while collecting resources.
    #   : '-I' packages to add to base "include" set, here it is the android.jar of the target-sdk.

    args.extend(['package', '-v', '-f', '-M', target.manifest,
                 '-S', target.resource_dir, '-I'])

    if self._forced_target_sdk:
      args.append(self.android_jar_tool(self._forced_target_sdk))
    else:
      args.append(self.android_jar_tool(target.target_sdk))

    if self._forced_ignored_assets:
      args.extend(['--ignore-assets', self._forced_ignored_assets])
    else:
      args.extend(['--ignore-assets', self.IGNORED_ASSETS])

    # extend -F bin/*apk $INPUT_DIRS

    log.debug('Executing: {0}'.format(args))
    return args

  def execute(self):
    print ("EXECUTING")
    safe_mkdir(self.workdir)
    with self.context.new_workunit(name='apk-bundle', labels=[WorkUnit.MULTITOOL]):
      targets = self.context.targets(self.is_app)
      #TODO (MATEOR) invalidation machinery
      for target in targets:
        mapping = self.context.products.get('dex')
        print((mapping))
        print("THAT WAS A GOOD DRUM BREAK")
        for basedir in mapping.get(target):
          dex_dir = basedir
        print(dex_dir)
      targets = self.context.targets(self.is_android)
      for target in targets:
        print(target)
        #resources = self.context.products.get('java')
        #resources_from_target = resources.get(target)

        new_resources = self.context.products.get('android-gen')
        print ((new_resources))
        if new_resources.get(target) is not None:
          for basedir in new_resources.get(target):
            greg = basedir
          print (greg)
        else:
          print("JIMINIY CRICKET")
          #@for prod in products:
            #print(prod)