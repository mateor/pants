# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import logging
import os
import subprocess

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
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
  Handle the processing of resources for Android targets with the
  Android Asset Packaging Tool (aapt).

  The aapt tool supports 6 major commands: [dump, list, add, remove, crunch, package]
  For right now, pants is only supporting 'package'. More to come as we support Release builds
  (crunch, at minimum).

  Commands and flags for aapt can be seen here:
  https://android.googlesource.com/platform/frameworks/base/+/master/tools/aapt/Command.cpp
  """

  @classmethod
  def _calculate_genfile(cls, package):
    return os.path.join(cls.package_path(package), 'R.java')

  @staticmethod
  def is_aapt_target(target):
    """Return True if target has class files to be compiled into dex."""
    return isinstance(target, AndroidBinary)

  @classmethod
  def product_types(cls):
    return ['java']

  def __init__(self, *args, **kwargs):
    super(AaptGenerate, self).__init__(*args, **kwargs)
    self._jar_library_by_sdk = {}

  def create_sdk_jar_deps(self, targets):
    # prepare exactly N android jar targets where N is the number of SDKs in-play
    sdks = set(ar.target_sdk for ar in targets)
    for sdk in sdks:
      jar_url = 'file://{0}'.format(self.android_jar_tool(sdk))
      jar = JarDependency(org='com.google', name='android', rev=sdk, url=jar_url)
      address = SyntheticAddress(self.workdir, 'android-{0}.jar'.format(sdk))
      self._jar_library_by_sdk[sdk] = self.context.add_new_target(address, JarLibrary, jars=[jar])

  def _render_args(self, target, sdk, resource_dirs, output_dir):
    """Compute the args that will be passed to the aapt tool."""

    # Glossary of used aapt flags. Aapt handles a ton of action, this will continue to expand.
    #   : 'package' is the main aapt operation (see class docstring for more info).
    #   : '-m' is to "make" a package directory under location '-J'.
    #   : '-J' Points to the output directory.
    #   : '-M' is the AndroidManifest.xml of the project.
    #   : '-S' points to the list of resource_dir to 'scan' while collecting resources.
    #   : '-I' packages to add to base 'include' set, here it is the android.jar of the target-sdk.
    args = [self.aapt_tool(target.build_tools_version)]
    args.extend(['package', '-m', '-J', output_dir])
    args.extend(['-M', target.manifest.path])
    args.append('--auto-add-overlay')
    while resource_dirs:
      # Priority for resources is left->right, so reverse the order it was collected (DFS preorder).
      args.extend(['-S', resource_dirs.pop()])
    args.extend(['-I', self.android_jar_tool(sdk)])
    args.extend(['--ignore-assets', self.ignored_assets])
    logger.debug('Executing: {0}'.format(' '.join(args)))
    return args

  def execute(self):
    # Every android_binary and each of their android_library dependencies must have their resources
    # processed into R.Java files. The libraries are processed using the SDK version of the dependee
    # android_binary. The number of R.java files produced from each library is <= # of sdks in play.
    targets = self.context.targets(self.is_aapt_target)
    self.create_sdk_jar_deps(targets)
    for target in targets:
      sdk = target.target_sdk
      outdir = self.aapt_out(sdk)

      gentargets = [target]
      def gather_gen_targets(tgt):
        """Gather all targets that might have an AndroidResources dependency."""
        if isinstance(tgt, AndroidLibrary):
          gentargets.append(tgt)
      target.walk(gather_gen_targets)

      # A target's resources, as well as the resources of its transitive deps, are needed.
      for targ in gentargets:
        # TODO(mateo) hook in invalidation. Adding it here doesn't work because the invalidation
        # framework can't differentiate between one library compiled by multiple sdks.
        resource_dirs = []

        for dep in targ.closure():
          if isinstance(dep, AndroidResources):
            resource_dirs.append(dep.resource_dir)

        args = self._render_args(targ, sdk, resource_dirs, outdir)
        with self.context.new_workunit(name='aapt_gen', labels=[WorkUnit.MULTITOOL]) as workunit:
          returncode = subprocess.call(args, stdout=workunit.output('stdout'),
                                       stderr=workunit.output('stderr'))
          if returncode:
            raise TaskError('The AaptGen process exited non-zero: {0}'.format(returncode))
        self.createtarget(targ, sdk)

  def createtarget(self, gentarget, sdk):
    spec_path = os.path.join(os.path.relpath(self.aapt_out(sdk), get_buildroot()))
    address = SyntheticAddress(spec_path=spec_path, target_name=gentarget.id)
    aapt_gen_file = self._calculate_genfile(gentarget.manifest.package_name)
    deps = [self._jar_library_by_sdk[sdk]]
    tgt = self.context.add_new_target(address,
                                      JavaLibrary,
                                      derived_from=gentarget,
                                      sources=[aapt_gen_file],
                                      dependencies=deps)
    gentarget.inject_dependency(tgt.address)


  def aapt_out(self, sdk):
    outdir = os.path.join(self.workdir, sdk)
    safe_mkdir(outdir)
    return outdir
