# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from contextlib import contextmanager
import os
import textwrap

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.util.contextutil import temporary_dir, temporary_file
from pants_test.tasks.test_base import TaskTest



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
