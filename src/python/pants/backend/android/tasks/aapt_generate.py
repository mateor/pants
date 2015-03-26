# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import logging
import os
import subprocess
from collections import defaultdict

from twitter.common.collections import OrderedSet

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.android.targets.android_target import AndroidTarget
from pants.backend.android.tasks.aapt_task import AaptTask
from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.backend.jvm.targets.java_library import JavaLibrary
from pants.base.address import SyntheticAddress
from pants.base.build_environment import get_buildroot
from pants.base.exceptions import TaskError
from pants.base.workunit import WorkUnit
from pants.util.dirutil import safe_mkdir


logger = logging.getLogger(__name__)

class AaptGenerate(AaptTask):
  """
  Compile java classes into dex files, Dalvik executables.
  """

  @classmethod
  def _calculate_genfile(cls, package):
    return os.path.join(cls.package_path(package), 'R.java')

  @staticmethod
  def is_aapt_target(target):
    """Return True if target has class files to be compiled into dex."""
    return isinstance(target, AndroidBinary)

  @staticmethod
  def is_gentarget(target):
    """Return True if target has class files to be compiled into dex."""
    return isinstance(target, AndroidResources)

  @classmethod
  def product_types(cls):
    return ['java']

  def __init__(self, *args, **kwargs):
    super(AaptGenerate, self).__init__(*args, **kwargs)
    self._jar_library_by_sdk = {}
    self.sdks = {}

  def prepare_gen(self, targets):
    # prepare exactly N android jar targets where N is the number of SDKs in-play
    sdks = set(ar.target_sdk for ar in targets)
    for sdk in sdks:
      jar_url = 'file://{0}'.format(self.android_jar_tool(sdk))
      jar = JarDependency(org='com.google', name='android', rev=sdk, url=jar_url)
      address = SyntheticAddress(self.workdir, '{0}-jars'.format(sdk))
      self._jar_library_by_sdk[sdk] = self.context.add_new_target(address, JarLibrary, jars=[jar])

  def _render_args(self, target, used_sdk, resource_dirs, output_dir):
    """Compute the args that will be passed to the aapt tool."""
    args = []

    # Glossary of used aapt flags. Aapt handles a ton of action, this will continue to expand.
    #   : 'package' is the main aapt operation (see class docstring for more info).
    #   : '-m' is to "make" a package directory under location '-J'.
    #   : '-J' Points to the output directory.
    #   : '-M' is the AndroidManifest.xml of the project.
    #   : '-S' points to the resource_dir to "spider" down while collecting resources.
    #   : '-I' packages to add to base "include" set, here it is the android.jar of the target-sdk.
    args.extend([self.aapt_tool(target.build_tools_version)])
    args.extend(['package', '-m', '-J', output_dir])
    args.extend(['-M', target.manifest.path])
    args.append('--auto-add-overlay')
    while resource_dirs:
      # Priority for resources is left->right, so reverse the order it was collected (DFS preorder).
      args.extend(['-S', resource_dirs.pop()])
    args.extend(['-I', self.android_jar_tool(used_sdk)])
    args.extend(['--ignore-assets', self.ignored_assets])
    logger.debug('Executing: {0}'.format(' '.join(args)))
    return args


  def execute(self):

    print("WE RUN THIS")
    targets = self.context.targets(self.is_aapt_target)
    self.prepare_gen(targets)
    # with self.invalidated(targets) as invalidation_check:
    #   invalid_targets = []
    #   for vt in invalidation_check.invalid_vts:
    #     invalid_targets.extend(vt.targets)
    #   for target in invalid_targets:
    for target in targets:
      sdk = target.target_sdk
      self.sdks[target] = sdk

      outdir = self.aapt_out(target)

      deps = [target]
      #sdks[target] = target.target_sdk
      def get_aapt_targets(tgt):
        if isinstance(tgt, AndroidLibrary):
          print("The get_aapt_target: ", tgt)
          self.sdks[tgt] = sdk
          deps.append(tgt)

      target.walk(get_aapt_targets)

      for targ in deps:
        print("WE ARE AAPOTING: ", targ)
        resource_dirs = []

        def get_resource_dirs(tgt):
          """Get path of all resource_dirs that are depended on by the target."""
          if isinstance(tgt, AndroidResources):
            print("We are resourcing: ", tgt)
            self.sdks[tgt] = sdk
            resource_dirs.append(os.path.join(get_buildroot(), tgt.resource_dir))

        target.walk(get_resource_dirs)


        args = self._render_args(targ, self.sdks[targ], resource_dirs, outdir)
        with self.context.new_workunit(name='aapt_gen', labels=[WorkUnit.MULTITOOL]) as workunit:
          returncode = subprocess.call(args, stdout=workunit.output('stdout'),
                                       stderr=workunit.output('stderr'))
          if returncode:
            raise TaskError('The AaptGen process exited non-zero: {0}'.format(returncode))
      gentargets_by_dependee = self.context.dependents(
        on_predicate=self.is_aapt_target,
        from_predicate=lambda t: not self.is_aapt_target(t)
        )
      dependees_by_gentarget = defaultdict(set)
      for dependee, tgts in gentargets_by_dependee.items():
        for gentarget in tgts:
          dependees_by_gentarget[gentarget].add(dependee)
      for t in gentargets_by_dependee:
        self.createtarget(targ, dependees_by_gentarget.get(targ, []))

    for target in targets:
      #self.context.products.get('dex').add(target, self.dx_out(target)).append(self.DEX_NAME)
      pass


  def createtarget(self, gentarget, dependees):
    print("SDKS: ", self.sdks)
    print("GENTARGET: ", gentarget)
    spec_path = os.path.join(os.path.relpath(self.aapt_out(gentarget), get_buildroot()))
    address = SyntheticAddress(spec_path=spec_path, target_name=gentarget.id)
    aapt_gen_file = self._calculate_genfile(gentarget.manifest.package_name)
    deps = OrderedSet([self._jar_library_by_sdk[self.sdks[gentarget]]])
    tgt = self.context.add_new_target(address,
                                      JavaLibrary,
                                      derived_from=gentarget,
                                      sources=[aapt_gen_file],
                                      dependencies=deps)
    for dependee in dependees:
      dependee.inject_dependency(tgt.address)
    return tgt

  def aapt_out(self, target):
    outdir = os.path.join(self.workdir, self.sdks[target])
    safe_mkdir(outdir)
    return outdir
