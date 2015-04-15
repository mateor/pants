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

  def __init__(self, *args, **kwargs):
    super(ExplodeAar, self).__init__(*args, **kwargs)
    self._classes_jar_by_target = {}

  def create_classes_jar_target(self, target, jar_files):
    """Create a JarLibrary target for each the jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    # Prepare exactly N android jar targets where N is the number of SDKs in-play.
    jar_deps = []
    for jar in jar_files:
      jar_url = 'file://{0}'.format(jar)
      name = '{}-{}'.format(target.id, os.path.basename(jar))
      print("NAME IS:", name)
      jar_deps.append(JarDependency(org=target.manifest.package_name,
                                    # TODO FIX REVISION
                                    name=name, rev='100', url=jar_url))
      address = SyntheticAddress(self.workdir, '{}-library.jar'.format(name))
    new_target = self.context.add_new_target(address, JarLibrary, jars=jar_deps)
    target.inject_dependency(new_target.address)

  def create_resource_target(self, target, resource_dir):
    """Create a JarLibrary target for each the jar included within every AndroidLibrary dependency.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    # Prepare exactly N android jar targets where N is the number of SDKs in-play.

    jar_url = 'file://{0}'.format(self.android_jar_tool(jar))
    jar = JarDependency(org='com.google', name='android', rev=sdk, url=jar_url)
    address = SyntheticAddress(self.workdir, 'android-{0}.jar'.format(sdk))
    self._jar_library_by_sdk[sdk] = self.context.add_new_target(address, JarLibrary, jars=[jar])

  def _unpack_jar(self, jar):
    pass

  def execute(self):
    targets = self.context.targets(self.is_library)
    print("LADIES AND GENTLEMEN WE ARE FLOATING IN THE EXPLODE_AAR TASK....")
    unpacked_archives = self.context.products.get('ivy_imports')   #jarmap = products[unpacked_jars]
    print("UNPACKED_ARCHIVES: ", unpacked_archives)
    for target in targets:
      libraries = unpacked_archives.get(target)
      print("LIBRARIES: ", libraries)
      # Separating libraries by id is safe because each target has a consistent filter pattern.
      # TODO(mateor) investigate moving the filter to the repack in dxcompile. Unpacking under
      # target.id could mean that jars are unpacked multiple times if they are defined in multiple
      # specs. Moving the filtering to dxCompile would reduce the unpacking load.
      outdir = os.path.join(self.workdir, target.id)
      for items in libraries:
        # Put in invalidation(here looks right).
        for archive in libraries[items]:
          jar_files = []
          print("HERE ARE THE ITEMS: ", archive)
          if archive.endswith('.jar'):
            unzip_target = os.path.join(items, archive)
            jar_files.append(unzip_target)
            print("EW FOUND AN JAR FILE: ", jar_files)
          elif archive.endswith('.aar'):
            print("EW FOUND AN AAR: ", archive)
            destination = os.path.join(self.workdir, archive)
            ZIP.extract(os.path.join(items, archive), destination)
            unzip_target = os.path.join(destination, 'classes.jar')
            resource_dir = os.path.join(destination, 'res')
            if os.path.isfile(unzip_target):
              print("WE FOUND A CLASSES.JAR", unzip_target)
              jar_files.append(unzip_target)
              self.create_classes_jar_target(target, jar_files)
            if os.path.isfile(resource_dir):
              print("WE FOUND A RESOURCE DIR", resource_dir)
              self.create_resource_target(target, resource_dir)

          #safe_mkdir(outdir)
          print("THE CLASSPATH OBJECTS ARE: ", libraries)
          # If the library was an aar file then there is a classes.jar to inject into the target graph.
        print("INCLUDES ARE: ", target.include_patterns)
        unpack_filter = self._calculate_unpack_filter(target)

        ZIP.extract(unzip_target, outdir, filter_func=unpack_filter)
        print("WE EXTARCTED YALL")
