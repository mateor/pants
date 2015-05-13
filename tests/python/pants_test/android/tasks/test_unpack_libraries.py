# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
import shutil
from contextlib import contextmanager
from textwrap import dedent

from pants.backend.android.targets.android_dependency import AndroidDependency
from pants.backend.android.targets.android_library import AndroidLibrary
from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.android.tasks.unpack_libraries import UnpackLibraries
from pants.backend.core.targets.dependencies import Dependencies
from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.backend.jvm.tasks.ivy_imports import IvyImports
from pants.backend.jvm.tasks.ivy_task_mixin import IvyTaskMixin
from pants.base.build_file_aliases import BuildFileAliases
from pants.fs.archive import ZIP
from pants.util.contextutil import open_zip, temporary_dir, temporary_file
from pants.util.dirutil import safe_mkdir, safe_open, safe_walk, touch
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
      # Create classes.jar.
      with self.sample_jarfile(location):
        pass
#      touch(os.path.join(location, 'classes.jar'))
    if resources:
      safe_mkdir(os.path.join(location, 'res'))
    yield location

  @contextmanager
  # TODO(standardize between sample_jarfile and sample_aarfile.)
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

  def test_ivy_args(self):
    # A regression test for ivy_mixin_task. UnpackLibraries depends on the mapped jar filename being
    # unique and including the version number. If you are making a change to
    # ivy_task_mixin._get_ivy_args() that maintains those properties, feel free to update this test.
    ivy_args = [
      '-retrieve', '{}/[organisation]/[artifact]/[conf]/'
                   '[organisation]-[artifact]-[revision](-[classifier]).[ext]'.format('foo'),
      '-symlink',
      ]
    self.assertEqual(ivy_args, IvyTaskMixin._get_ivy_args('foo'))

  # Test unpacking process.


  # There is a bit of fudging here. In practice, the jar name is transformed by ivy into
  # '[organisation]-[artifact]-[revision](-[classifier]).[ext]'. The unpack_libraries task does not
  # care about the details of the imported jar name but it does rely on that name being unique and
  # including the version number. When adding a dummy product this test class preemptively mimics
  # that naming structure in order to mock the filename of mapped jars.
  def _make_android_dependency(self, name, library_file, version):
    build_file = os.path.join(self.build_root, 'unpack', 'libs', 'BUILD')
    if os.path.exists(build_file):
      os.remove(build_file)
    self.add_to_build_file('unpack/libs', dedent('''
      android_dependency(name='{name}',
        jars=[
          jar(org='com.example', name='bar', rev='{version}', url='file:///{filepath}'),
        ],
      )
    '''.format(name=name, version=version, filepath=library_file)))
    #import pdb; pdb.set_trace()

  def _add_dummy_product(self, foo_target, android_dep, unpack_task):
    ivy_imports_product = unpack_task.context.products.get('ivy_imports')
    ivy_imports_product.add(foo_target, os.path.dirname(android_dep),
                            [os.path.basename(android_dep)])

  # TODO UPdate params to be descripti
  def _approximate_ivy_mapjar_name(self, aar_archive, android_archive):
    location = os.path.dirname(aar_archive)
    ivy_mapjar_name = os.path.join(location,
                                   '{}{}'.format(android_archive, os.path.splitext(aar_archive)[1]))
    shutil.copy(aar_archive, ivy_mapjar_name)
    return ivy_mapjar_name

  def test_aar_file(self):
    with temporary_dir() as temp:
      with self.sample_aarfile('org.pantsbuild.android.test', temp) as aar_archive:
        self.add_to_build_file('unpack', dedent('''
        android_library(name='test',
          libraries=['unpack/libs:test-jar'],
          include_patterns=[
            'a/b/c/*.class',
          ],
         )
        '''))
        self._make_android_dependency('test-jar', aar_archive, '0.0.2')
        test_target = self.target('unpack:test')
        task = self.create_task(self.context(target_roots=[test_target]))

        # fudge
        for android_archive in test_target.imported_jars:
          target_jar = self._approximate_ivy_mapjar_name(aar_archive, android_archive)
          self._add_dummy_product(test_target, target_jar, task)
        task.execute()
        aar_name = os.path.basename(target_jar)
        files = []
        jar_location = task.unpack_jar_location(aar_name)
        for _, dirname, filename in safe_walk(jar_location):
          files += filename
        self.assertIn('Foo.class', files)

      # Add sentinel file to the archive without bumping the version.
        with open_zip(aar_archive, 'w') as library:
          library.writestr('a/b/c/Baz.class', 'Baz')

        # Calling the task a second time will not unpack the target so the sentinel is not found.
        for android_archive in test_target.imported_jars:
          target_jar = self._approximate_ivy_mapjar_name(aar_archive, android_archive)
          self._add_dummy_product(test_target, target_jar, task)
        task.execute()
        files = []
        aar_name = os.path.basename(target_jar)
        jar_location = task.unpack_jar_location(aar_name)
        for _, dirname, filename in safe_walk(jar_location):
          files.extend(filename)
        self.assertNotIn('Baz.class', files)

        # Bump the version and the archive is unpacked and the class is found.
        self.reset_build_graph()  # Forget about the old definition of the unpack/jars:foo-jar target

        self._make_android_dependency('test-jar', aar_archive, '0.0.3')
        #test_target = self.target('unpack:test')
        #task = self.create_task(self.context(target_roots=[test_target]))
        for android_archive in test_target.imported_jars:

          target_jar = self._approximate_ivy_mapjar_name(aar_archive, android_archive)

          self._add_dummy_product(test_target, target_jar, task)
          import pdb; pdb.set_trace()
        task.execute()
        aar_name = os.path.basename(target_jar)
        jar_location = task.unpack_jar_location(aar_name)

        files = []
        for _, dirname, filename in safe_walk(jar_location):
          files.extend(filename)
        self.assertIn('Baz.class', files)
