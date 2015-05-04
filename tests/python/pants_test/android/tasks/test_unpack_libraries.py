# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
from contextlib import contextmanager

from pants.backend.android.targets.android_resources import AndroidResources
from pants.backend.android.tasks.unpack_libraries import UnpackLibraries
from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.util.contextutil import open_zip, temporary_dir, temporary_file
from pants_test.android.test_android_base import TestAndroidBase


class UnpackLibrariesTest(TestAndroidBase):
  """Test the .aar and .jar unpacking methods in pants.backend.android.tasks.unpack_libraries."""

  @classmethod
  def task_type(cls):
    return UnpackLibraries

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
        created_target = task.create_classes_jar_target(android_library,
                                                        'org.pantsbuild.example-1.0', jar)
        self.assertEqual(created_target.derived_from, android_library)
        self.assertTrue(created_target.is_synthetic)
        self.assertTrue(isinstance(created_target, JarLibrary))

  def test_create_resource_target(self):
    with self.android_library() as android_library:
      with temporary_file() as manifest:
        manifest.write(self.android_manifest())
        manifest.close()
        with temporary_dir() as res:
          task = self.create_task(self.context())
          created_target = task.create_resource_target(android_library,
                                                                'org.pantsbuild.example-1.0',
                                                                manifest.name,
                                                                res)
          self.assertEqual(created_target.derived_from, android_library)
          self.assertTrue(created_target.is_synthetic)
          self.assertTrue(isinstance(created_target, AndroidResources))
          self.assertEqual(created_target.resource_dir, res)
          self.assertEqual(created_target.manifest.path, manifest.name)

  def test_create_android_library_target(self):
    with self.android_library(include_patterns=['**/*.class']) as android_library:
      pass

  @contextmanager
  def sample_jarfile(self):
    """Create a jar file with a/b/c/data.txt and a/b/c/foo.proto"""
    with temporary_dir() as temp_dir:
      jar_name = os.path.join(temp_dir, 'foo.jar')
      with open_zip(jar_name, 'w') as library:
        library.writestr('a/b/c/Foo.class', 'Foo text')
        library.writestr('a/b/c/Bar.class', 'message Foo {}')
      yield jar_name
