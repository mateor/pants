# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.tasks.sign_apk import SignApkTask
from pants.base.exceptions import TaskError
from pants.util.contextutil import temporary_dir, temporary_file
from pants_test.android.test_android_base import TestAndroidBase
from pants_test.tasks.task_test_base import TaskTestBase


class UnpackedLibrariesTest(TaskTestBase):
  """Test the package signing methods in pants.backend.android.tasks.SignApk"""

  _TEST_KEYSTORE = '%(homedir)s/.doesnt/matter/keystore_config.ini'

  @classmethod
  def task_type(cls):
    return SignApkTask
