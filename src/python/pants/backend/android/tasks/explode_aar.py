# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.android.tasks.android_task import AndroidTask
from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.backend.jvm.targets.java_library import JavaLibrary
from pants.backend.jvm.tasks.unpack_jars import UnpackJars
from pants.base.address import SyntheticAddress
from pants.base.build_environment import get_buildroot
from pants.fs.archive import ZIP
from pants.util.dirutil import safe_mkdir


class ExplodeAar(UnpackJars):

  class InvalidLibraryFile(Exception):
    """Indicates an invalid android manifest."""

  @classmethod
  def prepare(cls, options, round_manager):
    super(ExplodeAar, cls).prepare(options, round_manager)
    #round_manager.require_data('unpacked_archives')

    #round_manager.require_data('jar_dependencies')

  @classmethod
  def product_types(cls):
    return ['exploded_aars']

  @staticmethod
  def is_library(target):
    """Return True for AndroidLibrary targets."""
    return isinstance(target, AndroidLibrary) or isinstance(target, AndroidBinary)

  def __init__(self, *args, **kwargs):
    super(ExplodeAar, self).__init__(*args, **kwargs)
    self._created_targets = {}

  def create_classes_jar_target(self, target, archive, jar):
    """Create a JarLibrary target for each jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    print("JAR TARGET: ", archive, jar)
    if os.path.isfile(jar):
      jar_url = 'file://{0}'.format(jar)
      name = '{}-jar'.format(archive)
      jar_dep = (JarDependency(org=target.id,
                                    # TODO FIX REVISION
                                    name=archive, rev='100', url=jar_url))
      address = SyntheticAddress(self.workdir, '{}-{}.jar'.format(target.id, archive))
      new_target = self.context.add_new_target(address, JarLibrary, jars=[jar_dep],
                                               derived_from=target)
      #target.inject_dependency(new_target.address)
     # return [new_target]
    return []

  def create_resource_target(self, target, archive, manifest, resource_dir):
    """Create a JarLibrary target for each the jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    if os.path.isdir(resource_dir):
      address = SyntheticAddress(self.workdir, '{}-resources'.format(archive))
      new_target = self.context.add_new_target(address, AndroidResources,
                                               manifest=manifest, resource_dir=resource_dir,
                                               derived_from=target)
      #target.inject_dependency(new_target.address)
      return [new_target]
    return []

  def create_android_library_target(self, target, archive, manifest, resource_dir, jar_target):
    print("resource dir IN CREATE_TARGET", resource_dir)
    deps = self.create_resource_target(target, archive, manifest, resource_dir)
    print("LIBRARIES DEPS ARE ", deps)
    libraries = self.create_classes_jar_target(target, archive, jar_target)
    address = SyntheticAddress(self.workdir, '{}-{}-android_library'.format(archive, target.id))
    new_target = self.context.add_new_target(address, AndroidLibrary,
                                             manifest=manifest,
                                             libraries=libraries,
                                             include_patterns=target.include_patterns,
                                             exclude_patterns=target.exclude_patterns,
                                             dependencies=deps,
                                             derived_from=target)
  #target.inject_dependency(new_target.address)
    return new_target

  def _unpack_jar(self, jar):
    pass

  def execute(self):
    targets = self.context.targets(self.is_library)
    print("TARGETS: ", targets)
    unpacked_archives = self.context.products.get('ivy_imports')
    print("IMPORTS: ", unpacked_archives)
    for target in targets:
      imports = unpacked_archives.get(target)

      # TODO(mateor) investigate moving the filter to the repack in dxcompile. Unpacking under
      # target.id could mean that jars are unpacked multiple times if they are defined in multiple
      # specs. Moving the filtering to dxCompile would reduce the unpacking load.

      # Separating libraries by target.id is safe b/c each target has a consistent filter pattern.

      if imports:

        for archive_path in imports:
          for archive in imports[archive_path]:

            # InVALIDATION?
            outdir = os.path.join(self.workdir, target.id, archive)

            if archive.endswith('.jar'):
              unpack_candidate = os.path.join(archive_path, archive)
            elif archive.endswith('.aar'):
              # Unpack .aar files to reveal products.
              unpacked_aar_destination = os.path.join(self.workdir, archive)
              unpack_candidate = os.path.join(unpacked_aar_destination, 'classes.jar')

              # INVALIDATION
              ZIP.extract(os.path.join(archive_path, archive), unpacked_aar_destination)

            # Unpack jar for inclusion in apk file.
            if os.path.isfile(unpack_candidate):
              ZIP.extract(unpack_candidate, outdir)
              #INVALIDATION

          if archive not in self._created_targets:
              print("WE ARE CREATING A TRAGET: ", archive)
              manifest = os.path.join(unpacked_aar_destination, 'AndroidManifest.xml')
              jar_file = os.path.join(unpacked_aar_destination, 'classes.jar')
              resource_dir = os.path.join(unpacked_aar_destination, 'res')

              # TODO add another JAr for every jar under 'libs'.





              if os.path.isfile(manifest):
                print("WE ARE CREATING A NEW ANDROIDLB For : ")
                new_target = self.create_android_library_target(target, archive, manifest, resource_dir,
                                                                jar_file)
                self._created_targets[archive] = new_target
              # else:
                #     raise self.InvalidLibraryFile("An android_library's .aar file must contain a "
                #                                    "AndroidManifest.xml: {}".format(self))

          #HACK
          if archive.endswith('.aar'):
            target.inject_dependency(self._created_targets[archive].address)





            #safe_mkdir(outdir)
              # If the library was an aar file then there is a classes.jar to inject into the target graph.

           # unpack_filter = self._calculate_unpack_filter(target)


          print('EXPLODE OUTDIR: ', outdir)
          rel_unpack_dir = os.path.relpath(outdir, get_buildroot())

          self.context.products.get('unpacked_libraries').add(target, get_buildroot()).append(rel_unpack_dir)
          #unpacked_libraries = self.context.products.get_data('unpacked_libraries', lambda: {})
          #import pdb; pdb.set_trace()
          #unpacked_libraries[target].append(rel_unpack_dir)
    print("UNPAKCED_LIB: ", self.context.products.get('unpacked_libraries'))
