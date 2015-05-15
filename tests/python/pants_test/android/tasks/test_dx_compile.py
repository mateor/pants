# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
from collections import defaultdict
from textwrap import dedent

from pants.backend.android.tasks.dx_compile import DxCompile
from pants.goal.products import MultipleRootedProducts
from pants.util.contextutil import temporary_dir, temporary_file
from pants.util.dirutil import safe_rmtree
from pants_test.android.test_android_base import TestAndroidBase, distribution


class DxCompileTest(TestAndroidBase):
  """Test dex creation methods of pants.backend.android.tasks.DxCompile."""

  JAVA_CLASSES_LOC = '.pants.d/compile/java/classes'
  UNPACKED_LIBS_LOC = '.pants.d/unpack-jars/unpack-libs/explode-jars'

  @classmethod
  def task_type(cls):
    return DxCompile

  @staticmethod
  def base_files(version):
    java_classes = ['org.pantsbuild-example-{}/a/b/c/Foo.class'.format(version),
                    'org.pantsbuild-example-{}/a/b/c/Bar.class'.format(version),
                    'org.pantsbuild-example-{}/a/b/c/Baz.class'.format(version)]
    return java_classes

  def setUp(self):
    super(DxCompileTest, self).setUp()
    self.set_options(read_artifact_caches=None,
                     write_artifact_caches=None,
                     use_nailgun=False)
  def tearDown(self):
    # Delete any previously mocked files.
    safe_rmtree(os.path.join(self.build_root, self.JAVA_CLASSES_LOC))
    safe_rmtree(os.path.join(self.build_root, self.UNPACKED_LIBS_LOC))

  def _add_classes_by_target(self, context, target, files):
    # Create class files to mock the classes_by_target product.
    class_products = context.products.get_data('classes_by_target',
                                               lambda: defaultdict(MultipleRootedProducts))
    java_agent_products = MultipleRootedProducts()
    for class_file in files:
      self.create_file(os.path.join(self.JAVA_CLASSES_LOC, class_file), '0xCAFEBABE')
      file_path = os.path.join(self.build_root, self.JAVA_CLASSES_LOC)
      java_agent_products.add_rel_paths(file_path, ['{}'.format(class_file)])
    class_products[target] = java_agent_products
    return context

  def _add_unpacked_libraries_to_context(self, context, target, files):
    # Create class files to mock the unpack_libraries product.
    class_products = context.products.get_data('classes_by_target',
                                               lambda: defaultdict(MultipleRootedProducts))
    java_agent_products = MultipleRootedProducts()
    for class_file in files:
      self.create_file(os.path.join(self.JAVA_CLASSES_LOC, class_file), '0xCAFEBABE')
      file_path = os.path.join(self.build_root, self.JAVA_CLASSES_LOC)
      java_agent_products.add_rel_paths(file_path, ['{}'.format(class_file)])
    class_products[target] = java_agent_products
    return context

  def test_gather_javac_classes(self):
    with self.android_binary() as binary:
      # Add class files to classes_by_target.
      classes = self.base_files('1.0')
      context = self.context(target_roots=binary)
      task_context = self._add_classes_by_target(context, binary, classes)
      dx_task = self.create_task(task_context)

      # Test that the proper class files are gathered for inclusion in the dex file.
      class_files = dx_task._gather_classes(binary)
      for filename in classes:
        file_path = os.path.join(self.build_root, self.JAVA_CLASSES_LOC, filename)
        self.assertIn(file_path, class_files)

  def test_gather_javac_classes_from_deps(self):
    # Make sure classes are being gathered from library dependencies.
    with self.android_library() as android_library:
      with self.android_binary(dependencies=[android_library]) as binary:
        classes = self.base_files('1.0')
        context = self.context(target_roots=binary)
        task_context = self._add_classes_by_target(context, android_library, classes)
        dx_task = self.create_task(task_context)

        filtered_classes = dx_task._gather_classes(binary)
        for class_file in classes:
          file_path = os.path.join(self.build_root, self.JAVA_CLASSES_LOC, class_file)
          self.assertIn(file_path, filtered_classes)
