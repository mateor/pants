# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.targets.android_library import AndroidLibrary
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

  def create_classes_jar_target(self, target, classes_jar):
    """Create a JarLibrary target for the classes.jar that is required to be in every .aar archive.

    :param list targets: A list of AndroidBinary targets.
    """
    # Prepare exactly N android jar targets where N is the number of SDKs in-play.
    jar_url = 'file://{0}'.format(classes_jar)
    address = SyntheticAddress(self.workdir, 'android-{0}.jar'.format(target))
    unpacked = self._unpack_jar
    self.context.add_new_target(address, JavaLibrary, sources=[unpacked])

  def _unpack_jar(self, jar):
    pass

  def execute(self):
    targets = self.context.targets(self.is_library)
    print("LADIES AND GENTLEMEN WE ARE FLOATING IN THE EXPLODE_AAR TASK....")
    unpacked_archives = self.context.products.get('ivy_imports')   #jarmap = products[unpacked_jars]
    print("UNPACKED_ARCHIVES: ", unpacked_archives)
    for target in targets:
      unpacked_library = unpacked_archives.get(target)
      outdir = os.path.join(self.workdir, target.manifest.package_name)
      safe_mkdir(outdir)
      print("THE CLASSPATH OBJECTS ARE: ", unpacked_library)
      # If the library was an aar file then there is a classes.jar to inject into the target graph.
      if 'classes.jar' in unpacked_library[0]:
        classes_jar = os.path.join(unpacked_library[1], 'classes.jar')
        print("WE FOUND A CLASSES.JAR", classes_jar)
        print("INCLUDES ARE: ", target.include_patterns)
        unpack_filter = self._calculate_unpack_filter(target)
        ZIP.extract(classes_jar, outdir, filter_func=unpack_filter)
        print("WE EXTARCTED YALL")
