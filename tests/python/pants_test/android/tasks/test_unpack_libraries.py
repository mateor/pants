# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
from contextlib import contextmanager
from textwrap import dedent

from pants.backend.android.targets.android_dependency import AndroidDependency
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.android.tasks.unpack_libraries import UnpackLibraries
from pants.backend.core.targets.dependencies import Dependencies
from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.base.build_file_aliases import BuildFileAliases
from pants.fs.archive import ZIP
from pants.util.contextutil import open_zip, temporary_dir, temporary_file
from pants.util.dirutil import safe_mkdir, safe_open, touch
from pants_test.android.test_android_base import TestAndroidBase


class UnpackLibrariesTest(TestAndroidBase):
  """Test the .aar and .jar unpacking methods in pants.backend.android.tasks.unpack_libraries."""

  @classmethod
  def task_type(cls):
    return UnpackLibraries

  @property
  def alias_groups(self):
    return BuildFileAliases.create(
      targets={
        'android_dependency': AndroidDependency,
        'android_library': AndroidLibrary,
        'jar_library': JarLibrary,
        'target': Dependencies
      },
      objects={
        'jar': JarDependency,
      },
    )

  @contextmanager
  def unpacked_aar_library(self, location, manifest=True, classes_jar=True, resources=True):
    """Create the contents of an aar file, with optional components."""
    if manifest:
      manifest_file = os.path.join(location, 'AndroidManifest.xml')
      touch(manifest_file)
      with safe_open(manifest_file, 'w') as fp:
        fp.write(self.android_manifest())
        fp.close()
    if classes_jar:
      touch(os.path.join(location, 'classes.jar'))
    if resources:
      safe_mkdir(os.path.join(location, 'res'))
    yield location

  @contextmanager
  def sample_aarfile(self, name, location):
    """Create an aar file, using the contents created by self.unpacked_aar_library."""
    with temporary_dir() as temp:
      with self.unpacked_aar_library(temp) as aar_contents:
        archive = ZIP.create(aar_contents, location, name)
        aar = os.path.join(location, '{}.aar'.format(name))
        os.rename(archive, aar)
    yield aar

  @contextmanager
  def sample_jarfile(self, location=None, file_name=None):
    """Create a jar file."""
    name = file_name or 'classes.jar'
    jar_name = os.path.join(location, name)
    with open_zip(jar_name, 'w') as library:
      library.writestr('a/b/c/Foo.class', 'Foo')
      library.writestr('a/b/c/Bar.class', 'Bar')
    yield jar_name

  def _make_android_dependency(self, name, library_file, version):
    build_path = os.path.join(self.build_root, 'unpack', 'libs', 'BUILD')
    if os.path.exists(build_path):
      os.remove(build_path)
    self.add_to_build_file('unpack/libs', dedent('''
      android_dependency(name='{name}',
        jars=[
          jar(org='com.example', name='bar', rev='{version}', url='file:///{filepath}'),
        ],
      )
    '''.format(name=name, version=version, filepath=library_file)))

  def test_unpack_smoke(self):
    task = self.create_task(self.context())
    task.execute()

  def test_is_library(self):
    with self.android_library() as android_library:
      task = self.create_task(self.context())
      self.assertTrue(task.is_library(android_library))

  def test_aar_out(self):
    task = self.create_task(self.context())
    archive = 'org.pantsbuild.example-1.0'
    outdir = task.unpack_aar_location(archive)
    self.assertEqual(os.path.join(task.workdir, archive), outdir)

  def test_jar_out(self):
    task = self.create_task(self.context())
    archive = 'org.pantsbuild.example-1.0'
    outdir = task.unpack_jar_location(archive)
    self.assertEqual(os.path.join(task.workdir, 'explode-jars', archive), outdir)

  def test_create_classes_jar_target(self):
    with self.android_library() as android_library:
      with temporary_file() as jar:
        task = self.create_task(self.context())
        archive = 'org.pantsbuild.example-1.0'
        created_target = task.create_classes_jar_target(android_library, archive, jar)
        self.assertEqual(created_target.derived_from, android_library)
        self.assertTrue(created_target.is_synthetic)
        self.assertTrue(isinstance(created_target, JarLibrary))

  def test_create_resource_target(self):
    with self.android_library() as android_library:
      with temporary_file() as manifest:
        with temporary_dir() as res:
          manifest.write(self.android_manifest())
          manifest.close()
          task = self.create_task(self.context())
          archive = 'org.pantsbuild.example-1.0'
          created_target = task.create_resource_target(android_library, archive, manifest.name, res)

          self.assertEqual(created_target.derived_from, android_library)
          self.assertTrue(created_target.is_synthetic)
          self.assertTrue(isinstance(created_target, AndroidResources))
          self.assertEqual(created_target.resource_dir, res)
          self.assertEqual(created_target.manifest.path, manifest.name)

  def test_create_android_library_target(self):
    with self.android_library(include_patterns=['**/*.class']) as android_library:
      with temporary_dir() as temp:
        with self.unpacked_aar_library(temp) as contents:
          task = self.create_task(self.context())
          archive = 'org.pantsbuild.example-1.0'
          created_library = task.create_android_library_target(android_library, archive, contents)

          self.assertEqual(created_library.derived_from, android_library)
          self.assertTrue(created_library.is_synthetic)
          self.assertTrue(isinstance(created_library, AndroidLibrary))
          self.assertEqual(android_library.include_patterns, created_library.include_patterns)
          self.assertEqual(android_library.exclude_patterns, created_library.exclude_patterns)
          self.assertEqual(len(created_library.dependencies), 2)
          for dep in created_library.dependencies:
            isinstance(dep, AndroidResources) or isinstance(dep, JarLibrary)

  def test_no_classes_jar(self):
    with self.android_library(include_patterns=['**/*.class']) as android_library:
      with temporary_dir() as temp:
        with self.unpacked_aar_library(temp, classes_jar=False) as contents:
          task = self.create_task(self.context())
          archive = 'org.pantsbuild.example-1.0'
          created_library = task.create_android_library_target(android_library, archive, contents)
          self.assertEqual(len(created_library.dependencies), 1)
          for dep in created_library.dependencies:
            isinstance(dep, AndroidResources)

  def test_no_resources(self):
    with self.android_library() as android_library:
      with temporary_dir() as temp:
        with self.unpacked_aar_library(temp, classes_jar=False) as contents:
          task = self.create_task(self.context())
          archive = 'org.pantsbuild.example-1.0'
          created_library = task.create_android_library_target(android_library, archive, contents)
          self.assertEqual(len(created_library.dependencies), 1)
          for dep in created_library.dependencies:
            isinstance(dep, JarLibrary)

  def test_no_manifest(self):
    with self.assertRaises(UnpackLibraries.MissingElementException):
      with self.android_library(include_patterns=['**/*.class']) as android_library:
        with temporary_dir() as temp:
          with self.unpacked_aar_library(temp, manifest=False) as contents:
            task = self.create_task(self.context())
            archive = 'org.pantsbuild.example-1.0'
            task.create_android_library_target(android_library, archive, contents)

  # Test unpacking process.
  def test_aar_file(self):
    with temporary_dir() as temp:
      with self.sample_aarfile('org.pantsbuild.android.test', temp) as aar_archive:
        assert(os.path.isfile(aar_archive))  # DEBUG
        print("ARCHIVE: ", aar_archive)
        self.add_to_build_file('unpack', dedent('''
        android_library(name='test',
          libraries=['unpack/libs:test-jar'],
          include_patterns=[
            'a/b/c/*.class',
          ],
         )
        '''))
    self._make_android_dependency('test-jar', aar_archive, '0.0.1')
    test_target = self.target('unpack:test')
