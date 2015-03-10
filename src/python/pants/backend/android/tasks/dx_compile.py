# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
from hashlib import sha1

from twitter.common.collections import OrderedSet

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.tasks.android_task import AndroidTask
from pants.backend.jvm.tasks.nailgun_task import NailgunTask
from pants.base.exceptions import TaskError
from pants.base.workunit import WorkUnit
from pants.util.dirutil import safe_mkdir
from pants.fs.archive import ZIP
from pants.base.build_environment import get_buildroot


class DxCompile(AndroidTask, NailgunTask):
  """
  Compile java classes into dex files, Dalvik executables.
  """

  # name of output file. "Output name must end with one of: .dex .jar .zip .apk or be a directory."
  DEX_NAME = 'classes.dex'

  @staticmethod
  def is_dextarget(target):
    """Return True if target has class files to be compiled into dex."""
    return isinstance(target, AndroidBinary)

  @classmethod
  def register_options(cls, register):
    super(DxCompile, cls).register_options(register)
    register('--build-tools-version',
             help='Create the dex file using this version of the Android build tools.')
    register('--jvm-options', action='append', metavar='<option>...',
             help='Run dx with these JVM options.')

  @classmethod
  def product_types(cls):
    return ['dex']

  @classmethod
  def prepare(cls, options, round_manager):
    super(DxCompile, cls).prepare(options, round_manager)
    round_manager.require_data('classes_by_target')
    round_manager.require_data('unpacked_archives')

  def __init__(self, *args, **kwargs):
    super(DxCompile, self).__init__(*args, **kwargs)
    self._forced_build_tools_version = self.get_options().build_tools_version
    self._forced_jvm_options = self.get_options().jvm_options

    self.setup_artifact_cache()

  def _jars_to_directories(self, target):
    """Extracts and maps jars to directories containing their contents.

    :returns: a set of filepaths to directories containing the contents of jar.
    """
    files = set()
    jarmap = self.context.products.get('ivy_imports')
    print("JARMAP IS: ", jarmap)
    classmap = self.context.products.get('unpacked_archives')
    print("CLASSMAP IS: ", classmap)
    for folder, names in jarmap.by_target[target].items():
      for name in names:
        files.add(self._extract_jar(os.path.join(folder, name)))
    return files

  def _extract_jar(self, jar_path):
    """Extracts the jar to a subfolder of workdir/extracted and returns the path to it."""
    with open(jar_path, 'rb') as f:
      outdir = os.path.join(self.workdir, 'extracted', sha1(f.read()).hexdigest())
    if not os.path.exists(outdir):
      ZIP.extract(jar_path, outdir)
      self.context.log.debug('Extracting jar at {jar_path}.'.format(jar_path=jar_path))
    else:
      self.context.log.debug('Jar already extracted at {jar_path}.'.format(jar_path=jar_path))
    return outdir

  def _dx_path_imports(self, dx_targets):
    for target in dx_targets:
      for path in self._jars_to_directories(target):
        yield os.path.relpath(path, get_buildroot())

  def _render_args(self, outdir, classes):
    dex_file = os.path.join(outdir, self.DEX_NAME)
    args = []
    # Glossary of dx.jar flags.
    #   : '--dex' to create a Dalvik executable.
    #   : '--no-strict' allows the dx.jar to skip verifying the package path. This allows us to
    #            pass a list of classes as opposed to a top-level dir.
    #   : '--output' tells the dx.jar where to put and what to name the created file.
    #            See comment on self.classes_dex for restrictions.
    args.extend(['--dex', '--no-strict', '--output={0}'.format(dex_file)])

    # classes is a list of class files to be included in the created dex file.
    args.extend(classes)
    return args

  def _compile_dex(self, args, build_tools_version):
    if self._forced_build_tools_version:
      classpath = [self.dx_jar_tool(self._forced_build_tools_version)]
    else:
      classpath = [self.dx_jar_tool(build_tools_version)]

    jvm_options = self._forced_jvm_options if self._forced_jvm_options else None
    java_main = 'com.android.dx.command.Main'
    return self.runjava(classpath=classpath, jvm_options=jvm_options, main=java_main,
                        args=args, workunit_name='dx')

  def execute(self):
    with self.context.new_workunit(name='dx-compile', labels=[WorkUnit.MULTITOOL]):

      targets = self.context.targets(self.is_dextarget)

      bases = OrderedSet()
      bases.update(self._dx_path_imports(targets))
      print("RANDOM ASS DX IMPORTS ARE: ", bases)
      with self.invalidated(targets) as invalidation_check:
        invalid_targets = []
        for vt in invalidation_check.invalid_vts:
          invalid_targets.extend(vt.targets)
        for target in invalid_targets:
          outdir = self.dx_out(target)
          safe_mkdir(outdir)
          classes_by_target = self.context.products.get_data('classes_by_target')
          classes = []

          def add_to_dex(tgt):
            target_classes = classes_by_target.get(tgt)
            print("Target: ", tgt, " CLASSES: ", target_classes)
            if target_classes:

              def add_classes(target_products):
                for _, products in target_products.abs_paths():
                  for prod in products:
                    classes.append(prod)

              add_classes(target_classes)

          target.walk(add_to_dex)
          print("DX COMPILE classes : ", classes)
          if not classes:
            raise TaskError("No classes were found for {0!r}.".format(target))
          args = self._render_args(outdir, classes)
          print("ARGS for DX : ", ' '.join(args))
          # TODO (mateor) wrap this in a workunit and properly handle stdout/err.
          self._compile_dex(args, target.build_tools_version)
      for target in targets:
        self.context.products.get('dex').add(target, self.dx_out(target)).append(self.DEX_NAME)

  def dx_jar_tool(self, build_tools_version):
    """Return the appropriate dx.jar.

    :param string build_tools_version: The Android build-tools version number (e.g. '19.1.0').
    """
    dx_jar = os.path.join('build-tools', build_tools_version, 'lib', 'dx.jar')
    return self.android_sdk.register_android_tool(dx_jar)

  def dx_out(self, target):
    """Return the outdir for the DxCompile task."""
    return os.path.join(self.workdir, target.id)
