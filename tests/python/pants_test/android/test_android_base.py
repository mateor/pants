# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import textwrap

from contextlib import contextmanager

from pants.util.dirutil import chmod_plus_x, safe_open, touch
from pants.backend.android.targets.android_binary import AndroidBinary
from pants.util.contextutil import environment_as, temporary_dir, temporary_file
from pants_test.tasks.test_base import TaskTest

from twitter.common.collections import maybe_list


class TestAndroidBase(TaskTest):

  def android_binary(self):
    with temporary_file() as fp:
      fp.write(textwrap.dedent(
        """<?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android"
            package="com.pants.examples.hello" >
            <uses-sdk
                android:minSdkVersion="8"
                android:targetSdkVersion="19" />
        </manifest>
        """))
      path = fp.name
      fp.close()
      target = self.make_target(spec=':binary',
                                target_type=AndroidBinary,
                                manifest=path)
      return target

  @contextmanager
  # default for testing purposes being sdk 18 and 19, with latest build-tools 19.1.0
  def distribution(self, installed_sdks=('18', '19'),
                   installed_build_tools=('19.1.0', ),
                   files='android.jar',
                   executables=['aapt', 'zipalign']):
    with temporary_dir() as sdk:
      for sdks in installed_sdks:
        touch(os.path.join(sdk, 'platforms', 'android-' + sdks, files))
      for build in installed_build_tools:
        for exe in maybe_list(executables or ()):
          path = os.path.join(sdk, 'build-tools', build, exe)
          with safe_open(path, 'w') as fp:
            fp.write('')
          chmod_plus_x(path)
      yield sdk