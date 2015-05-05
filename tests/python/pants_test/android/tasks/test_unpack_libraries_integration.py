# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import pytest

from pants.util.contextutil import temporary_dir
from pants_test.android.android_integration_test import AndroidIntegrationTest


class UnpackLibrariesIntegrationTest(AndroidIntegrationTest):
  """Integration test for UnpackLibraries
  """

  # No android tools are needed but ANDROID_HOME needs to be set so we can fetch libraries from the
  # m2 repos included with the SDK.
  TOOLS = []
  tools = AndroidIntegrationTest.requirements(TOOLS)

  @pytest.mark.skipif('not UnpackLibrariesIntegrationTest.tools',
                      reason='UnpackLibraries integration test requires that ANDROID_HOME is set.')
  def test_library_unpack(self):
    with temporary_dir(root_dir=self.workdir_root()) as workdir:
      spec = 'examples/src/android/hello_with_library:'
      pants_run = self.run_pants_with_workdir(['unpack-jars', spec], workdir)
      self.assert_success(pants_run)
