# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from contextlib import contextmanager
import os
import textwrap


from pants.util.contextutil import temporary_file
from pants.util.contextutil import temporary_dir

from pants.backend.android.tasks.sign_apk import SignApkTask
from pants.backend.android.targets.android_binary import AndroidBinary
from pants.base.build_file_aliases import BuildFileAliases
from pants_test.tasks.test_base import TaskTest


class SignApkTest(TaskTest):
  """Test the package signing methods in pants.backend.android.tasks."""

  _DEFAULT_KEYSTORE = '%(homedir)s/.pants.d/android/keystore_config.ini'

  @classmethod
  def task_type(cls):
    return SignApkTask

  @property
  def alias_groups(self):
    return BuildFileAliases.create(targets={'android_binary': AndroidBinary})

  def _get_config(self,
                  section=SignApkTask._CONFIG_SECTION,
                  option='keystore_config_location',
                  location=_DEFAULT_KEYSTORE):
    ini = textwrap.dedent( """
    [{0}]

    {1}: {2}
    """).format(section, option, None)
    return ini

  def test_sign_apk_smoke(self):
    with temporary_dir() as publish_dir:
      task = self.prepare_task(config=self._get_config(location=None),
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      task.execute()
      task.config_file
      self.assertEquals(task.config_file, 3)