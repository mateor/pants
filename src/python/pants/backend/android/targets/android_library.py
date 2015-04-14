# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.backend.android.targets.android_target import AndroidTarget
from pants.backend.jvm.targets.import_jars_mixin import ImportJarsMixin
from pants.backend.jvm.targets.unpacked_jars import UnpackedJars
from pants.base.payload import Payload
from pants.base.payload_field import PrimitiveField


class AndroidLibrary(UnpackedJars, AndroidTarget):
  """Android library target as a jar."""

  def __init__(self, include_patterns=None, **kwargs):
    """
    :param list imports: List of addresses of `jar_library <#jar_library>`_
      targets.
    """
    self.include_patterns = kwargs.get('include_patterns', [])
    self.exclude_patterns = kwargs.get('exclude_patterns', [])

    print("KWARGS: ", kwargs)
    # TODO(BEFORE REVIEW: make 'libraries' just 'library' for android_library targets
    super(AndroidLibrary, self).__init__(**kwargs)
