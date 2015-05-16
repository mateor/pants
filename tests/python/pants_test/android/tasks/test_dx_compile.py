# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
from collections import defaultdict
from textwrap import dedent

from pants.backend.android.tasks.dx_compile import DxCompile
from pants.base.build_environment import get_buildroot
from pants.goal.products import MultipleRootedProducts
from pants.util.contextutil import temporary_dir, temporary_file
from pants.util.dirutil import safe_rmtree, touch
from pants_test.android.test_android_base import TestAndroidBase, distribution


class DxCompileTest(TestAndroidBase):
  """Test dex creation methods of pants.backend.android.tasks.DxCompile."""

  JAVA_CLASSES_LOC = os.path.join(get_buildroot(), '.pants.d/compile/java/classes')
  UNPACKED_LIBS_LOC = os.path.join(get_buildroot(),'.pants.d/unpack-jars/unpack-libs/explode-jars')

  @classmethod
  def task_type(cls):
    return DxCompile

  @classmethod
  def base_unpacked_files(cls, package, app, version):
    unpacked_classes = {}
    class_files = ['Example.class', 'Hello.class', 'World.class']

    # This is the name of the directory that holds the unpacked libs - modeled after jar_target.id.
    unpacked_location = '{}-{}-{}.aar'.format(package, app, version)
    unpacked_classes[unpacked_location] = []
    for filename in class_files:
      new_file = os.path.join('a/b/c', filename)
      touch(os.path.join(cls.UNPACKED_LIBS_LOC, unpacked_location, new_file))
      unpacked_classes[unpacked_location].append(new_file)
    return unpacked_classes


  @staticmethod
  def base_files(package, app):
    javac_classes = []
    class_files = ['Foo.class', 'Bar.class', 'Baz.class']
    for filename in class_files:
      javac_classes.append('{}/{}/a/b/c/{}'.format(package, app, filename))
    return javac_classes


  def setUp(self):
    super(DxCompileTest, self).setUp()
    self.set_options(read_artifact_caches=None,
                     write_artifact_caches=None,
                     use_nailgun=False)
  def tearDown(self):
    # Delete any previously mocked files.
    safe_rmtree(self.JAVA_CLASSES_LOC)
    safe_rmtree(os.path.join(self.UNPACKED_LIBS_LOC))

  def _mock_classes_by_target_product(self, context, target, files):
    # Create class files to mock the classes_by_target product.
    class_products = context.products.get_data('classes_by_target',
                                               lambda: defaultdict(MultipleRootedProducts))
    java_agent_products = MultipleRootedProducts()
    for class_file in files:
      self.create_file(os.path.join(self.JAVA_CLASSES_LOC, class_file), '0xCAFEBABE')
      java_agent_products.add_rel_paths(self.JAVA_CLASSES_LOC, ['{}'.format(class_file)])
    class_products[target] = java_agent_products
    return context

  def _mock_unpacked_libraries_product(self, context, target, unpacked):
    # Create class files to mock the unpack_libraries product.
    for archive in unpacked:
      relative_unpack_dir = (os.path.join(self.UNPACKED_LIBS_LOC, archive))

      unpacked_products = context.products.get('unpacked_libraries')
      unpacked_products.add(target, self.build_root).append(relative_unpack_dir)
    return context

  def test_gather_classes(self):
    with self.android_binary() as binary:
      # Add class files to classes_by_target product.
      context = self.context(target_roots=binary)
      classes = self.base_files('org.pantsbuild.android', 'example')
      task_context = self._mock_classes_by_target_product(context, binary, classes)
      dx_task = self.create_task(task_context)

      # Test that the proper class files are gathered for inclusion in the dex file.
      class_files = dx_task._gather_classes(binary)
      for filename in classes:
        file_path = os.path.join(self.JAVA_CLASSES_LOC, filename)
        self.assertIn(file_path, class_files)

  def test_gather_classes_from_deps(self):
    # Make sure classes are being gathered from a binary's android_library dependencies.
    with self.android_library() as android_library:
      with self.android_binary(dependencies=[android_library]) as binary:
        context = self.context(target_roots=binary)
        classes = self.base_files('org.pantsbuild.android', 'example')
        task_context = self._mock_classes_by_target_product(context, android_library, classes)
        dx_task = self.create_task(task_context)

        gathered_classes = dx_task._gather_classes(binary)
        for class_file in classes:
          file_path = os.path.join(self.JAVA_CLASSES_LOC, class_file)
          self.assertIn(file_path, gathered_classes)

  def test_gather_unpacked_libs(self):
    with self.android_library() as android_library:
      with self.android_binary(dependencies=[android_library]) as binary:
        context = self.context(target_roots=binary)
        classes = self.base_unpacked_files('org.pantsbuild.android', 'example', '1.0')
        task_context = self._mock_unpacked_libraries_product(context, android_library, classes)
        dx_task = self.create_task(task_context)

        gathered_classes = dx_task._gather_classes(binary)
        for location in classes:
          for class_file in classes[location]:
            file_path = os.path.join(self.UNPACKED_LIBS_LOC, location, class_file)
            self.assertIn(file_path, gathered_classes)

  def test_gather_both_javac_and_unpacked_classes(self):
    with self.android_library() as android_library:
      with self.android_binary(dependencies=[android_library]) as binary:
        context = self.context(target_roots=binary)
        classes_by_target = self.base_files('org.pantsbuild.android', 'example')
        unpacked_classes = self.base_unpacked_files('org.pantsbuild.android', 'example', '1.0')
        task_context = self._mock_classes_by_target_product(context, android_library, classes_by_target)
        both_context = self._mock_unpacked_libraries_product(task_context, android_library, unpacked_classes)
        dx_task = self.create_task(both_context)

        gathered_classes = dx_task._gather_classes(binary)

        # Test that compiled classes are gathered for dex file.
        for class_file in classes_by_target:
          file_path = os.path.join(self.JAVA_CLASSES_LOC, class_file)
          self.assertIn(file_path, gathered_classes)

        # Test that unpacked classes are gathered for dex file.
        for location in unpacked_classes:
          for class_file in unpacked_classes[location]:
            file_path = os.path.join(self.UNPACKED_LIBS_LOC, location, class_file)
            self.assertIn(file_path, gathered_classes)

  def test_file_filter_in_gather_classes(self):
    with self.android_library(include_patterns=['**/a/**/Example.class']) as android_library:
      with self.android_binary(dependencies=[android_library]) as binary:
        context = self.context(target_roots=binary)
        classes = self.base_unpacked_files('org.pantsbuild.android', 'example', '1.0')
        task_context = self._mock_unpacked_libraries_product(context, android_library, classes)
        dx_task = self.create_task(task_context)

        gathered_classes = dx_task._gather_classes(binary)
        for location in classes:
          included_file = os.path.join(self.UNPACKED_LIBS_LOC, location, 'a/b/c/Example.class')
          excluded_file = os.path.join(self.UNPACKED_LIBS_LOC, location, 'a/b/c/Hello.class')
          self.assertIn(included_file, gathered_classes)
          self.assertNotIn(excluded_file, gathered_classes)
