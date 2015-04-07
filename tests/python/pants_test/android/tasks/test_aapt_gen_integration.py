# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

import pytest

from pants_test.android.android_integration_test import AndroidIntegrationTest


class AaptGenIntegrationTest(AndroidIntegrationTest):
  """Integration test for AaptGen

  The Android SDK is modular, finding an SDK on the PATH is no guarantee that there is
  a dx.jar anywhere on disk. The TOOLS are the ones required by the target in 'test_aapt_gen'
  method. If you add a target, you may need to expand the TOOLS list and perhaps define new
  BUILD_TOOLS or TARGET_SDK class variables.
  """

  TOOLS = [
    os.path.join('build-tools', AndroidIntegrationTest.BUILD_TOOLS, 'aapt'),
    os.path.join('platforms', 'android-' + AndroidIntegrationTest.TARGET_SDK, 'android.jar')
  ]

  tools = AndroidIntegrationTest.requirements(TOOLS)

  @pytest.mark.skipif('not AaptGenIntegrationTest.tools',
                      reason='Android integration test requires tools {0!r} '
                             'and ANDROID_HOME set in path.'.format(TOOLS))
  def test_aapt_gen(self):
    self.aapt_gen_test(AndroidIntegrationTest.TEST_TARGET)

  def aapt_gen_test(self, target):
    pants_run = self.run_pants(['dex', target])
    self.assert_success(pants_run)
