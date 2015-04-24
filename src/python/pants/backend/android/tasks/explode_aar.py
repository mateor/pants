# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.backend.jvm.tasks.unpack_jars import UnpackJars
from pants.base.address import SyntheticAddress
from pants.base.build_environment import get_buildroot
from pants.fs.archive import ZIP


class ExplodeAar(UnpackJars):

  class InvalidLibraryFile(Exception):
    """Indicates an invalid android manifest."""

  @classmethod
  def prepare(cls, options, round_manager):
    super(ExplodeAar, cls).prepare(options, round_manager)

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

  def create_classes_jar_target(self, target, archive, jar_file):
    """Create a JarLibrary target containing a JarDependency from the jar_file.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """
    # Try to parse revision number. This is just to satisfy the spec, the rev is part of jar_file.
    archive_version = os.path.splitext(archive)[0].rpartition('-')[-1]
    jar_url = 'file://{0}'.format(jar_file)
    jar_dep = (JarDependency(org=target.id, name=archive, rev=archive_version, url=jar_url))
    address = SyntheticAddress(self.workdir, '{}-classes.jar'.format(archive))
    new_target = self.context.add_new_target(address, JarLibrary, jars=[jar_dep],
                                             derived_from=target)
    return new_target


  def create_resource_target(self, target, archive, manifest, resource_dir):
    """Create an AndroidResources target.

    :param list targets: A list of AndroidBinary targets.
    :param list targets: A list of AndroidBinary targets.
    """

    address = SyntheticAddress(self.workdir, '{}-resources'.format(archive))
    new_target = self.context.add_new_target(address, AndroidResources,
                                             manifest=manifest, resource_dir=resource_dir,
                                             derived_from=target)
    return new_target

  def create_android_library_target(self, target, archive, manifest, resource_dir, jar_target):
    deps = []
    if os.path.isdir(resource_dir):
      deps.append(self.create_resource_target(target, archive, manifest, resource_dir))
    if os.path.isfile(jar_target):
      deps.append(self.create_classes_jar_target(target, archive, jar_target))
    address = SyntheticAddress(self.workdir, '{}-{}-android_library'.format(archive, target.id))
    new_target = self.context.add_new_target(address, AndroidLibrary,
                                             manifest=manifest,
                                             include_patterns=target.include_patterns,
                                             exclude_patterns=target.exclude_patterns,
                                             dependencies=deps,
                                             derived_from=target)
    return new_target

  def _unpack_jar(self, jar):
    pass

  def execute(self):
    # TODO(mateor) add AndroidBinary support. If there is no need for include/exclude, an
    #  android_binary should be able to simply declare an android_dependency as a dep and work.

    targets = self.context.targets(self.is_library)
    unpacked_archives = self.context.products.get('ivy_imports')
    for target in targets:
      imports = unpacked_archives.get(target)

      if imports:

        for archive_path in imports:
          for archive in imports[archive_path]:
            outdir = os.path.join(self.workdir, 'exploded-jars', archive)

            # InVALIDATION?

            if archive.endswith('.jar'):
              unpack_candidate = os.path.join(archive_path, archive)
            elif archive.endswith('.aar'):
              # Unpack .aar files to reveal products.
              unpacked_aar_destination = os.path.join(self.workdir, archive)
              unpack_candidate = os.path.join(unpacked_aar_destination, 'classes.jar')

              # INVALIDATION
              ZIP.extract(os.path.join(archive_path, archive),
                          unpacked_aar_destination)

            # Unpack jar for inclusion in apk file.
            if os.path.isfile(unpack_candidate):
              ZIP.extract(unpack_candidate, outdir)
              #INVALIDATION

          if archive not in self._created_targets:
            manifest = os.path.join(unpacked_aar_destination, 'AndroidManifest.xml')
            jar_file = os.path.join(unpacked_aar_destination, 'classes.jar')
            resource_dir = os.path.join(unpacked_aar_destination, 'res')

            # TODO(mateor) add another JarDependency for every jar under 'libs'.





            if os.path.isfile(manifest):
              print("WE ARE CREATING A NEW ANDROIDLB For : ")
              new_target = self.create_android_library_target(target, archive, manifest, resource_dir,
                                                              jar_file)
              self._created_targets[archive] = new_target
            else:
              raise self.InvalidLibraryFile('An android_library .aar file must contain an '
                                            'AndroidManifest.xml: {}'.format(archive))

          #HACK
          if archive.endswith('.aar'):
            # WHat if no target was made? error catch.
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
