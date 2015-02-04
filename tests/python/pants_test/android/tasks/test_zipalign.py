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
from pants_test.tasks.test_base import TaskTest
from pants.util.contextutil import temporary_dir, temporary_file


class TestZipalign(TaskTest):
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

  def test_sign_apk_smoke(self):
    task = self.prepare_task(build_graph=self.build_graph,
                             build_file_parser=self.build_file_parser)
    task.execute()

    print("ZIPFILE: ", (self.archive()))