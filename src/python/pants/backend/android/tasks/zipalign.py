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
  def prepare(cls, options, round_manager):
    super(Zipalign, cls).prepare(options, round_manager)
    # Zipalign is a no-op on 'debug_apk' but requires both so as to bundle their tasks into a goal.
    round_manager.require_data('release_apk')
    round_manager.require_data('debug_apk')

  @staticmethod
  def is_zipaligntarget(target):
    return isinstance(target, AndroidBinary)

  def __init__(self, *args, **kwargs):
    super(Zipalign, self).__init__(*args, **kwargs)
    self._android_dist = self.android_sdk

  def execute(self):
    print("WE are in ZIPalign!")


    #TODO(BEFORE REVIEW: MOve the SignAPk products away from dist.) Zipalign is where we wil release.