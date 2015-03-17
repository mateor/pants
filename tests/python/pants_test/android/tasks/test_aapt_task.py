# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.tasks.aapt_gen import AaptTask
from pants_test.android.test_android_base import TestAndroidBase


class TestAaptTask(TestAndroidBase):
  """Test the AaptTask base class."""


  def test_package_path(self):
    self.assertEqual(os.path.join('com', 'pants', 'example', 'tests'),
                     AaptTask.package_path('com.pants.example.tests'))

  def test_package_path(self):
    self.assertEqual('com', AaptTask.package_path('com'))

  def test_aapt_tool(self):
    with self.distribution() as dist:
      with self.android_binary() as android_binary:
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_binary
        self.assertEqual(task.aapt_tool(target),
                         os.path.join(dist, 'build-tools', target.build_tools_version, 'zipalign'))
