# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.manifest_parser import ManifestParser
from pants.backend.jvm.targets.jvm_target import JvmTarget
from pants.base.exceptions import TargetDefinitionException


class AndroidTarget(JvmTarget):
  """A base class for all Android targets."""


  def __init__(self,
               address=None,
               # TODO (mateor) add support for minSDk
               # most recent build_tools_version should be defined elsewhere
               build_tools_version="19.1.0",
               manifest=None,
               **kwargs):
    """
    :param build_tools_version: API for the Build Tools (separate from SDK version).
      Defaults to the latest full release.
    :param manifest: path/to/file of 'AndroidManifest.xml' (required name). Paths are relative
      to the BUILD file's directory.
    """
    super(AndroidTarget, self).__init__(address=address, **kwargs)
    self.add_labels('android')
    self._manifest = manifest
    # TODO(pl): These attributes should live in the payload
    self.build_tools_version = build_tools_version

    # TODO (BEFORE REVIEW) Fix this temporary hack
    self.address = address

    self._manifest = manifest
    self._manifest_path = None

    self._package = None
    self._target_sdk = None

    self._app_name = None

  @property
  def manifest(self):
    # TODO (BEFORE REVIEW) find a sensible way to fallback to any AndroidManifest in the target home.
    if self._manifest_path is None:
      if self._manifest is None:
        raise TargetDefinitionException(self, 'Android targets require a manifest attribute.')
      manifest = os.path.join(self.address.spec_path, self._manifest)
      if not os.path.isfile(manifest):
        raise TargetDefinitionException(self, 'The given manifest {0} is not a file '
                                              'at path {1}'.format(self._manifest, manifest))
      self._manifest_path = manifest
    return self._manifest_path

  @property
  def package(self):
    if self._package is None:
      self._package = ManifestParser.get_package_name(self)
    return self._package

  @property
  def target_sdk(self):
    if self._target_sdk is None:
      self._target_sdk = ManifestParser.get_target_sdk(self)
    return self._target_sdk

  @property
  def app_name(self):
    # If unable to parse application name, silently falls back to target name.
    if self._app_name is None:
      self._app_name = ManifestParser.get_app_name(self)
    if self._app_name is None:
      self._app_name = self.name
    return self._app_name