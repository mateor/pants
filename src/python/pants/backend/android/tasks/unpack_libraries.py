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


class UnpackLibraries(Task):

  class MissingUnpackedDirsError(Exception):
    """Raised if a directory that is expected to be unpacked doesn't exist."""

  class MultipleDependencyVersions(Exception):
    """Raised when multiple copies of the same class are added to the product."""

  @classmethod
  def prepare(cls, options, round_manager):
    super(UnpackLibraries, cls).prepare(options, round_manager)

  @classmethod
  def product_types(cls):
    return ['unpacked_libraries']

  @staticmethod
  def is_library(target):
    """Return True for AndroidLibrary targets."""
    # TODO(mateor) add AndroidBinary support. If include/exclude patterns aren't needed, an
    #  android_binary should be able to simply declare an android_dependency as a dependency.
    return isinstance(target, AndroidLibrary)

  @staticmethod
  def is_app(target):
    """Return True for AndroidBinary targets."""
    return isinstance(target, AndroidBinary)

  def __init__(self, *args, **kwargs):
    super(UnpackLibraries, self).__init__(*args, **kwargs)
    self._created_targets = {}
    self._archive_paths = {}
    self._unpacked_archives = {}
    self._archives_per_target = {}

  def create_classes_jar_target(self, target, archive, jar_file):
    """Create a JarLibrary target containing the jar_file as a JarDependency.

    :param Target target: AndroidTarget that the new JarDependency derives from.
    :param string archive: An archive name as fetched by ivy, e.g. 'org.pantsbuild.example-1.0.aar'.
    :param string jar_file: Full path of the classes.jar contained within aar files.
    :returns: JarLibrary target
    """
    # TODO(mateor) add another JarDependency for every jar under 'libs'.

    # Try to parse revision number. This is just to satisfy the spec, the rev is part of 'archive'.
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

  def create_android_library_target(self, target, archive):

    """Create an AndroidResources target.

    Every aar file will be unpacked and the contents used to create a new AndroidLibrary
    target.

    :param Target target: AndroidTarget that the new AndroidLibrary target derives from.
    :param string archive: An archive name as fetched by ivy, e.g. 'org.pantsbuild.example-1.0.aar'.
    :param string unpacked_aar_location: Full path of dir holding contents of an unpacked aar file.
    :returns: AndroidLibrary target
    """
    # The following three elements of an aar file have names mandated by the aar spec:
    #   http://tools.android.com/tech-docs/new-build-system/aar-format
    # They are said to be mandatory although in practice that assumption only holds for manifest.
    unpacked_aar_location = self.unpack_aar_location(archive)
    manifest = os.path.join(unpacked_aar_location, 'AndroidManifest.xml')
    jar_file = os.path.join(unpacked_aar_location, 'classes.jar')
    resource_dir = os.path.join(unpacked_aar_location, 'res')

    # Sanity-check to make sure all aaars we expect to be unpacked are actually unpacked.
    if not os.path.isfile(manifest):
      raise self.MissingUnpackedDirsError("An AndroidManifest.xml is expected in every unpacked "
                                          ".aar file but none was found in the {} archive "
                                          "for the {} target".format(manifest, target))
    deps = []
    if os.path.isdir(resource_dir):
      deps.append(self.create_resource_target(target, archive, manifest, resource_dir))
    if os.path.isfile(jar_file):
      deps.append(self.create_classes_jar_target(target, archive, jar_file))
    address = SyntheticAddress(self.workdir, '{}-android_library'.format(archive))
    new_target = self.context.add_new_target(address, AndroidLibrary,
                                             manifest=manifest,
                                             include_patterns=target.include_patterns,
                                             exclude_patterns=target.exclude_patterns,
                                             dependencies=deps,
                                             derived_from=target)
    return new_target

  def execute(self):

    targets = self.context.targets(self.is_app)
    ivy_imports = self.context.products.get('ivy_imports')

    for target in targets:
      transitive_deps = self.context.build_graph.transitive_subgraph_of_addresses([target.address])
      library_deps = [t for t in transitive_deps if isinstance(t, AndroidLibrary)]

      # Gather and dedupe archives per target.
      for library in library_deps:
        imports = ivy_imports.get(library)
        if imports:
          for archive_path in imports:
            for archive in imports[archive_path]:
              if archive not in self._unpacked_archives:



                outdir = self.unpack_jar_location(archive)
                if archive.endswith('.jar'):
                  jar_file = os.path.join(archive_path, archive)
                elif archive.endswith('.aar'):
                  # Unpack .aar files to reveal products.
                  unpacked_aar_destination = self.unpack_aar_location(archive)
                  jar_file = os.path.join(unpacked_aar_destination, 'classes.jar')

                  # Unpack .aar files.
                  ZIP.extract(self._unpacked_archives[archive], unpacked_aar_destination)

                # Unpack jar for inclusion in apk file.
                if os.path.isfile(jar_file):
                  ZIP.extract(jar_file, outdir)

                self._unpacked_archives[archive] = jar_file
              if archive not in self._archives_per_target:
                self._archives_per_target[target] = archive

      #import pdb; pdb.set_trace()
      class_files = []
      unpacked_dirs = []
      for library in library_deps:
        imports = ivy_imports.get(library)
        if imports:
          for archive_path in imports:
            for archive in imports[archive_path]:
              # The contents of the unpacked aar file must be made into an AndroidLibrary target.
              if archive not in self._created_targets:
                new_target = self.create_android_library_target(library, archive)
                self._created_targets[archive] = new_target
              library.inject_dependency(self._created_targets[archive].address)


              file_filter = UnpackJars.get_unpack_filter(library)
              for root, dirpath, file_names in os.walk(self._unpacked_archives[archive]):
                for filename in file_names:
                  relative_dir = os.path.relpath(root, dirpath)

                  # Check against the library's include_patterns/exclude_patterns.
                  if file_filter(os.path.join(relative_dir, filename)):
                    if filename not in class_files:
                      class_files.append(filename)
                    else:
                      raise self.MultipleDependencyVersions("This class was already added")

                unpacked_dirs.append(os.path.join(root, filename))
                relative_unpack_dir = os.path.relpath(self.unpack_jar_location(archive), get_buildroot())
                exploded_products = self.context.products.get('unpacked_libraries')
                exploded_products.add(target, get_buildroot()).append(relative_unpack_dir)
                    #  target_archives = {}
    #
    # # Gather the archives each android package depends upon.
    # for android in targets:
    #   # Dedup archives per target.
    #   android_archives = set()
    #   transitive_deps = self.context.build_graph.transitive_subgraph_of_addresses([android.address])
    #   library_deps = [t for t in transitive_deps if isinstance(t, AndroidLibrary)]
    #   print("LIBRARY_DEPS: ", library_deps, android)
    #   for library in library_deps:
    #     imports = ivy_imports.get(library)
    #     if imports:
    #       print("IMPORTS: ", imports)
    #       for archive_path in imports:
    #         for archive in imports[archive_path]:
    #           if archive not in self._archive_paths:
    #             self._archive_paths[archive] = os.path.join(archive_path, archive)
    #           android_archives.update([archive])
    #   target_archives[android] = android_archives
    #
    #   print("ANDROID:        ARCHIVES: ", android, target_archives[android])
    #
    # with self.invalidated(targets) as invalidation_check:
    #   invalid_targets = []
    #   for vt in invalidation_check.invalid_vts:
    #     invalid_targets.extend(vt.targets)
    #   for target in invalid_targets:
    #     for archive in target_archives[target]:
    #       print("THIS TARGET: {}, and ARCHIVES: {}".format(target, target_archives))
    #       outdir = self.unpack_jar_location(archive)
    #
    #       if archive.endswith('.jar'):
    #         jar_file = self._archive_paths[archive]
    #       elif archive.endswith('.aar'):
    #         # Unpack .aar files to reveal products.
    #         unpacked_aar_destination = self.unpack_aar_location(archive)
    #         jar_file = os.path.join(unpacked_aar_destination, 'classes.jar')
    #
    #         # Unpack .aar files.
    #         ZIP.extract(self._archive_paths[archive], unpacked_aar_destination)
    #
    #       # Unpack jar for inclusion in apk file.
    #       if os.path.isfile(jar_file):
    #         ZIP.extract(jar_file, outdir)
    #         #INVALIDATION
    #
    # for target in self.context.targets(self.is_library):
    #   #binary_archives = target_archives[target]
    #   imports = ivy_imports.get(target)
    #   if imports:
    #     print("IMPORTS: ", imports)
    #     for archive_path in imports:
    #       for archive in imports[archive_path]:
    #         if archive.endswith('.aar'):
    #
    #           # The contents of the unpacked aar file must be made into an AndroidLibrary target.
    #           if archive not in self._created_targets:
    #             new_target = self.create_android_library_target(target, archive)
    #             self._created_targets[archive] = new_target
    #           print("INJECTING TARGET: {} /n with {}".format(target, self._created_targets[archive]))
    #           target.inject_dependency(self._created_targets[archive].address)
    #          # import pdb; pdb.set_trace()
    #         # The class files from the jars are packed into the classes.dex file during DxCompile.
    #         relative_unpack_dir = os.path.relpath(self.unpack_jar_location(archive), get_buildroot())
    #         exploded_products = self.context.products.get('unpacked_libraries')
    #         exploded_products.add(android, get_buildroot()).append(relative_unpack_dir)
    #     #import pdb; pdb.set_trace()


  def unpack_jar_location(self, archive):
    return os.path.join(self.workdir, 'explode-jars', archive)

  def unpack_aar_location(self, archive):
    return os.path.join(self.workdir, archive)
