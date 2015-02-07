# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import zipfile

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.tasks.zipalign import Zipalign
from pants.base.build_file_aliases import BuildFileAliases
from pants.util.contextutil import temporary_file
from pants_test.android.test_android_base import TestAndroidBase

class TestZipalign(TestAndroidBase):
  """Test class for the Zipalign task."""

  @classmethod
  def task_type(cls):
    return Zipalign

  @property
  def alias_groups(self):
    return BuildFileAliases.create(targets={'android_binary': AndroidBinary})

  def archive(self):
    with temporary_file() as fp:
      fp.write('Some contents')
      fp.close()
      path = fp.name
      for root, dirs, files in os.walk(path):
        for file in files:
          zipfile.write(os.path.join(root, file))
      return zipfile

  def test_zipalign_smoke(self):
    task = self.prepare_task(build_graph=self.build_graph,
                             build_file_parser=self.build_file_parser)
    task.execute()


    print("ZIPFILE: ", (self.archive()))

  def test_render_args(self):
    with self.distribution() as dist:
      task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist)],
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      target = self.android_binary()
      self.assertEqual(task.zipalign_binary(target), os.path.join(dist, 'build-tools', target.build_tools_version, 'zipalign'))