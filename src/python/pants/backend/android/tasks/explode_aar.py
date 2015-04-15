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

  @classmethod
  def prepare(cls, options, round_manager):
    super(ExplodeAar, cls).prepare(options, round_manager)
    round_manager.require_data('unpacked_archives')

    #round_manager.require_data('jar_dependencies')

  @classmethod
  def product_types(cls):
    return ['exploded_aars']

  @staticmethod
  def is_library(target):
    """Return True for AndroidLibrary targets."""
    return isinstance(target, AndroidLibrary)

  def create_classes_jar_target(self, target, jar_files):
    """Create a JarLibrary target for each the jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    # Prepare exactly N android jar targets where N is the number of SDKs in-play.
    jar_deps = []
    print("HERE ARE THE JAR_FIELS: ", jar_files)
    for jar in jar_files:
      jar_url = 'file://{0}'.format(jar_files[jar])
      name = '{}-jar'.format(jar)
      print("ORG IS: {} NAME IS: {}".format(jar, target.id))
      jar_deps.append(JarDependency(org=jar,
                                    # TODO FIX REVISION
                                    name=target.id, rev='100', url=jar_url))
    address = SyntheticAddress(self.workdir, '{}-library.jar'.format(name))
    new_target = self.context.add_new_target(address, JarLibrary, jars=jar_deps,
                                             derived_from=target)
    target.inject_dependency(new_target.address)

  def create_resource_target(self, target, archive, manifest, resource_dir):
    """Create a JarLibrary target for each the jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    # Prepare exactly N android jar targets where N is the number of SDKs in-play.
    address = SyntheticAddress(self.workdir, '{}-{}resources'.format(archive, target.id))
    new_target = self.context.add_new_target(address, AndroidResources,
                                             manifest=manifest,resource_dir=resource_dir,
                                             derived_from=target)
    target.inject_dependency(new_target.address)

  def _unpack_jar(self, jar):
    pass

  def execute(self):
    targets = self.context.targets(self.is_library)
    unpacked_archives = self.context.products.get('ivy_imports')
    print("UNPACKED_ARCHIVES: ", unpacked_archives)
    for target in targets:
      libraries = unpacked_archives.get(target)
      print("LIBRARIES: ", libraries)

      # TODO(mateor) investigate moving the filter to the repack in dxcompile. Unpacking under
      # target.id could mean that jars are unpacked multiple times if they are defined in multiple
      # specs. Moving the filtering to dxCompile would reduce the unpacking load.

      # Separating libraries by target.id is safe b/c each target has a consistent filter pattern.
      outdir = os.path.join(self.workdir, target.id)
      jar_files = {}
      for archive_path in libraries:
        # Put in invalidation(here looks right).

        for archive in libraries[archive_path]:
          print("HERE ARE THE ITEMS: ", archive)
          if archive.endswith('.jar'):
            jar_target = os.path.join(archive_path, archive)
            print("EW FOUND AN JAR FILE: ", jar_target)
          elif archive.endswith('.aar'):
            print("ARRRR FOUND AN AAR: ", archive)
            unpack_destination = os.path.join(self.workdir, archive)
            ZIP.extract(os.path.join(archive_path, archive), unpack_destination)
            manifest = os.path.join(unpack_destination, 'AndroidManifest.xml')
            jar_target = os.path.join(unpack_destination, 'classes.jar')
            resource_dir = os.path.join(unpack_destination, 'res')
            if os.path.isdir(resource_dir):
              print("WE FOUND A RESOURCE DIR", resource_dir)
              self.create_resource_target(target, archive, manifest, resource_dir)

            if os.path.isfile(jar_target):
              print("THIS IS A JAR TARGET", jar_target)
              jar_files[archive] = jar_target
              print("THIS CREATES THE JAR LIBRSRY FOR: ", jar_files)



          #safe_mkdir(outdir)
            # If the library was an aar file then there is a classes.jar to inject into the target graph.
          unpack_filter = self._calculate_unpack_filter(target)

          if os.path.isfile(jar_target):
            ZIP.extract(jar_target, outdir, filter_func=unpack_filter)
            print("WE EXTARCTED YALL")
      self.create_classes_jar_target(target, jar_files)
