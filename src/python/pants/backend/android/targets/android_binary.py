# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE)

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from pants.backend.android.targets.android_target import AndroidTarget
from pants.base.exceptions import TargetDefinitionException


class AndroidBinary(AndroidTarget):
  """Produces an Android binary."""

  def __init__(self,
               build_type=None,
               *args,
               **kwargs):
    """
    :param string name: The name of this target, which combined with this
      build file defines the :doc:`target address <target_addresses>`.
    :param sources: Source code files to compile. Paths are relative to the
      BUILD file's directory.
    :type sources: ``Fileset`` or list of strings.
    :param excludes: List of :ref:`exclude <bdict_exclude>`\s
      to filter this target's transitive dependencies against.
    :param build_tools_version: API for the Build Tools (separate from SDK version).
      Defaults to the latest full release.
    :param manifest: path/to/file of 'AndroidManifest.xml' (required name). Paths are relative
      to the BUILD file's directory.
    :param string build_type: One of [debug, release]. The keystore to sign the package with.
      Set as 'debug' by default.
    """
    super(AndroidBinary, self).__init__(*args, **kwargs)
    if build_type is None:
      self.build_type = 'debug'
    else:
      build_type = build_type.lower()
      if build_type == 'debug' or build_type == 'release':
        self.build_type = build_type
      else:
        raise TargetDefinitionException(self, "The 'build_type' must be either 'debug' or "
                                              "'release' instead of {0}".format(build_type))
