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
from pants_test.android.test_android_base import TestAndroidBase, distribution


class DxCompileTest(TestAndroidBase):
  """Test dex creation methods of pants.backend.android.tasks.DxCompile."""

  @classmethod
  def task_type(cls):
    return DxCompile

  def setUp(self):
    super(DxCompileTest, self).setUp()
    self.set_options(read_artifact_caches=None,
                     write_artifact_caches=None,
                     use_nailgun=False)

  def _add_classes_to_context(self, context, target, files):

    #dx_task = self.create_task(context)

    class_products = context.products.get_data('classes_by_target',
                                               lambda: defaultdict(MultipleRootedProducts))
    java_agent_products = MultipleRootedProducts()
    for class_file in files:
      self.create_file('.pants.d/unpack-jars/unpack-libs/{}'.format(class_file), '0xCAFEBABE string')
      file_location = os.path.join(self.build_root, '.pants.d/unpack-jars/unpack-libs')
      java_agent_products.add_rel_paths(file_location, ['{}'.format(class_file)])
    class_products[target] = java_agent_products
    print("CLASS PRODUCTS: ", class_products)

    return context


  def test_gather_files(self):
    with distribution() as dist:
      with self.android_library() as android_library:
        with self.android_binary(dependencies=[android_library]) as binary:
          files = ['org.pantsbuild.example/a/b/c/Foo.class',
                           'org.pantsbuild.example/a/b/c/Bar.class',
                           'org.pantsbuild.example/a/b/c/Baz.class',]
          context = self.context(target_roots=binary)

          task_context = self._add_classes_to_context(context, android_library, files)
          dx_task = self.create_task(task_context)
          print("TASK: ", dx_task.context.products.get_data('classes_by_target').get(android_library))
