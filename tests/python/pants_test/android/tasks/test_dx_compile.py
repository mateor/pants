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
    self.set_options(
      read_artifact_caches=None,
      write_artifact_caches=None)

  def test_gather_classes(self):
    with distribution() as dist:
      with self.android_library() as android_library:
        with self.android_binary(dependencies=[android_library]) as binary:
          context = self.context(target_roots=binary)
          dx_task = self.create_task(context)
          #jar_task = self.prepare_jar_task(context)

          class_products = context.products.get_data('classes_by_target',
                                                     lambda: defaultdict(MultipleRootedProducts))
          java_agent_products = MultipleRootedProducts()
          self.create_file('.pants.d/javac/classes/FakeAgent.class', '0xCAFEBABE')
          java_agent_products.add_rel_paths(os.path.join(self.build_root, '.pants.d/javac/classes'),
                                            ['FakeAgent.class'])
          class_products[binary] = java_agent_products

          print("CLASS PRODUCTS: ", class_products)
          print("TRAGET CLASSES: ", dx_task.context.products.get_data('classes_by_target').get(binary))
          import pdb; pdb.set_trace()
