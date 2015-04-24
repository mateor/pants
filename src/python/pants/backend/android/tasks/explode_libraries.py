# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.core.tasks.task import Task
from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.backend.jvm.tasks.unpack_jars import UnpackJars
from pants.base.address import SyntheticAddress
from pants.base.build_environment import get_buildroot
from pants.fs.archive import ZIP


class ExplodeLibraries(Task):

  @classmethod
  def prepare(cls, options, round_manager):
    super(ExplodeLibraries, cls).prepare(options, round_manager)

  @classmethod
  def product_types(cls):
    return ['exploded_libraries']

  @staticmethod
  def is_library(target):
    """Return True for AndroidLibrary targets."""
    return isinstance(target, AndroidLibrary) or isinstance(target, AndroidBinary)

  def __init__(self, *args, **kwargs):
    super(ExplodeLibraries, self).__init__(*args, **kwargs)
    self._created_targets = {}

  def create_classes_jar_target(self, target, archive, jar_file):
    """Create a JarLibrary target containing the jar_file as a JarDependency.

    :param Target target: AndroidTarget that the new JarDependency derives from.
    :param string archive: An archive name as fetched by ivy, e.g. 'org.pantsbuild.example-1.0.aar'.
    :param string jar_file: Full path of the classes.jar contained within aar files.
    :returns: JarLibrary target
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

    :param Target target: AndroidTarget that the new AndroidResources target derives from.
    :param string archive: An archive name as fetched by ivy, e.g. 'org.pantsbuild.example-1.0.aar'.
    :param string resource_dir: Full path of the res directory contained within aar files.
    :returns: AndroidResources target
    """

    address = SyntheticAddress(self.workdir, '{}-resources'.format(archive))
    new_target = self.context.add_new_target(address, AndroidResources,
                                             manifest=manifest, resource_dir=resource_dir,
                                             derived_from=target)
    return new_target

  def create_android_library_target(self, target, archive, unpacked_aar_location):

    """Create an AndroidResources target.

    :param Target target: AndroidTarget that the new AndroidLibrary target derives from.
    :param string archive: An archive name as fetched by ivy, e.g. 'org.pantsbuild.example-1.0.aar'.
    :param string unpacked_aar_location: Full path of dir holding contents of an unpacked aar file.
    :returns: AndroidLibrary target
    """
    # The following three elements of an aar file have names proscribed by the aar spec:
    #   http://tools.android.com/tech-docs/new-build-system/aar-format
    # They are said to be mandatory although in practice that assumption only holds for manifest.
    manifest = os.path.join(unpacked_aar_location, 'AndroidManifest.xml')
    jar_file = os.path.join(unpacked_aar_location, 'classes.jar')
    resource_dir = os.path.join(unpacked_aar_location, 'res')

    deps = []
    if os.path.isdir(resource_dir):
      deps.append(self.create_resource_target(target, archive, manifest, resource_dir))
    if os.path.isfile(jar_file):
      deps.append(self.create_classes_jar_target(target, archive, jar_file))
    address = SyntheticAddress(self.workdir, '{}-{}-android_library'.format(archive, target.id))
    new_target = self.context.add_new_target(address, AndroidLibrary,
                                             manifest=manifest,
                                             include_patterns=target.include_patterns,
                                             exclude_patterns=target.exclude_patterns,
                                             dependencies=deps,
                                             derived_from=target)
    return new_target

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



            # TODO(mateor) add another JarDependency for every jar under 'libs'.





          #HACK
          if archive.endswith('.aar'):
            # The contents of the unpacked aar file must be made into an AndroidLibrary target.
            if archive not in self._created_targets:
              new_target = self.create_android_library_target(target, archive,
                                                              unpacked_aar_destination)
              self._created_targets[archive] = new_target
            target.inject_dependency(self._created_targets[archive].address)


          # The class files from the jars are packed into the classes.dex file during DxCompile.
          rel_unpack_dir = os.path.relpath(outdir, get_buildroot())

          self.context.products.get('exploded_libraries').add(target, get_buildroot()).append(rel_unpack_dir)
          #unpacked_libraries = self.context.products.get_data('unpacked_libraries', lambda: {})
          #import pdb; pdb.set_trace()
          #unpacked_libraries[target].append(rel_unpack_dir)
