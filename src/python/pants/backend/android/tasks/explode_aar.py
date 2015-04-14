# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.android.tasks.android_task import AndroidTask
from pants.backend.jvm.targets.java_library import JavaLibrary
from pants.backend.jvm.tasks.unpack_jars import UnpackJars
from pants.base.address import SyntheticAddress
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

  def create_classes_jar_target(self, target, resource_dir):
    """Create a JarLibrary target for the classes.jar that is required to be in every .aar archive.

    :param list targets: A list of AndroidBinary targets.
    """
    # Prepare exactly N android jar targets where N is the number of SDKs in-play.
    jar_url = 'file://{0}'.format(resource_dir)
    address = SyntheticAddress(self.workdir, 'android-{0}.jar'.format(target))
    unpacked = self._unpack_jar
    self.context.add_new_target(address, AndroidResources, resource_dir=resource_dir)

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
      outdir = os.path.join(self.workdir, target.manifest.package_name)
      for items in libraries:
        for archive in libraries[items]:
          print("HERE ARE THE ITEMS: ", archive)
          if archive.endswith('.jar'):
            print("EW FOUND AN JAR FILE: ", archive)
            jar_file = os.path.join(outdir, archive)
          elif archive.endswith('.aar'):
            print("EW FOUND AN AAR: ", archive)
            destination = os.path.join(outdir, archive)
            ZIP.extract(os.path.join(items, archive), destination)
            classes_jar = os.path.join(destination, 'classes.jar')
            resource_dir = os.path.join(destination, 'res')
            if os.path.isfile(classes_jar):
              print("WE FOUND A CLASSES.JAR", classes_jar)
            jar_file = classes_jar
            if os.path.isfile(resource_dir):
              print("WE FOUND A RESOURCE DIR", resource_dir)
              self.create_classes_jar_target(resource_dir)

          #safe_mkdir(outdir)
          print("THE CLASSPATH OBJECTS ARE: ", libraries)
          # If the library was an aar file then there is a classes.jar to inject into the target graph.
        print("INCLUDES ARE: ", target.include_patterns)
        unpack_filter = self._calculate_unpack_filter(target)

     #   ZIP.extract(jar_file, outdir, filter_func=unpack_filter)
        print("WE EXTARCTED YALL")
