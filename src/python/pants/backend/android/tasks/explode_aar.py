# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

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
    return isinstance(target, AndroidLibrary)

  def __init__(self, *args, **kwargs):
    super(ExplodeAar, self).__init__(*args, **kwargs)
    self._created_targets = {}

  def create_classes_jar_target(self, target, archive, jar):
    """Create a JarLibrary target for each jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    print("WE ARE CREATING A TARGET: ", archive, jar)
    jar_url = 'file://{0}'.format(jar)
    name = '{}-jar'.format(archive)
    jar_dep = (JarDependency(org=archive,
                                  # TODO FIX REVISION
                                  name=target.id, rev='100', url=jar_url))
    address = SyntheticAddress(self.workdir, '{}-{}.jar'.format(target.id, archive))
    new_target = self.context.add_new_target(address, JarLibrary, jars=[jar_dep],
                                             derived_from=target)
    #target.inject_dependency(new_target.address)
    return new_target

  def create_resource_target(self, target, archive, manifest, resource_dir):
    """Create a JarLibrary target for each the jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    address = SyntheticAddress(self.workdir, '{}-{}resources'.format(archive, target.id))
    new_target = self.context.add_new_target(address, AndroidResources,
                                             manifest=manifest, resource_dir=resource_dir,
                                             derived_from=target)
    #target.inject_dependency(new_target.address)
    return new_target

  def create_android_library_target(self, target, archive, manifest, resource_dir, jar_target):
    if os.path.isdir(resource_dir):
      print("WE FOUND A RESOURCE DIR", resource_dir)
      resource_target = self.create_resource_target(target, archive, manifest, resource_dir)

  def _unpack_jar(self, jar):
    pass

  def execute(self):
    pass
    targets = self.context.targets(self.is_library)
    unpacked_archives = self.context.products.get('ivy_imports')
    print("UNPACKED_ARCHIVES: ", unpacked_archives)
    jar_libs = self.context.products.get('jar_map_default')
    print("JAR_LIBS IS : ", jar_libs)
    for target in targets:
      imports = unpacked_archives.get(target)
      print("LIBRARIES: ", imports)

      # TODO(mateor) investigate moving the filter to the repack in dxcompile. Unpacking under
      # target.id could mean that jars are unpacked multiple times if they are defined in multiple
      # specs. Moving the filtering to dxCompile would reduce the unpacking load.

      # Separating libraries by target.id is safe b/c each target has a consistent filter pattern.
      outdir = os.path.join(self.workdir, target.id)
      for archive_path in imports:

        for archive in imports[archive_path]:

          # InVALIDATION?

          print("HERE ARE THE ITEMS: ", archive)
          if archive.endswith('.jar'):
            jar_target = os.path.join(archive_path, archive)
            print("EW FOUND AN JAR FILE: ", jar_target)
          elif archive.endswith('.aar'):
            print("ARRRR FOUND AN AAR: ", archive)
            unpacked_aar_destination = os.path.join(self.workdir, archive)
            manifest = os.path.join(unpacked_aar_destination, 'AndroidManifest.xml')
            jar_target = os.path.join(unpacked_aar_destination, 'classes.jar')
            resource_dir = os.path.join(unpacked_aar_destination, 'res')

            # INVALIDATION
            ZIP.extract(os.path.join(archive_path, archive), unpacked_aar_destination)





            if os.path.isfile(manifest):
              print("THIS AAR HAS A MANIFEST", jar_target, archive)

              jar_dependency = self.create_classes_jar_target(target, archive, jar_target)

              self.create_android_library_target(target, archive, manifest, resource_dir, jar_dependency)

          # else:
          #     raise self.InvalidLibraryFile("An android_library's .aar file must contain a "
          #                                    "AndroidManifest.xml: {}".format(self))




          #safe_mkdir(outdir)
            # If the library was an aar file then there is a classes.jar to inject into the target graph.

        # TODO (MATEOR) move unpack to DXcompile to avoid multiple unapcks of archives.
         # unpack_filter = self._calculate_unpack_filter(target)

          if os.path.isfile(jar_target):
            ZIP.extract(jar_target, outdir, filter_func=None)
            print("WE EXTARCTED YALL")

            print("TESTING GLOBBING")
