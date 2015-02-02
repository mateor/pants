# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import logging

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.tasks.android_task import AndroidTask


class Zipalign(AndroidTask):
  """Task to run zipalign, which byte-orders signed apks."""

  @classmethod
  def prepare(self, options, round_manager):
    super(Zipalign, cls).prepare(options, round_manager)
    # Zipalign is a no-op on 'debug_apk' but requires both so as to bundle their tasks into a goal.
    round_manager.require_data('release_apk')
    round_manager.require_data('debug_apk')

  @staticmethod
  def is_zipaligntarget(target):
    return isinstance(target, AndroidBinary)
