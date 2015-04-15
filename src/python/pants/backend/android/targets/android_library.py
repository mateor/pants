# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.android_manifest_parser import AndroidManifestParser
from pants.backend.android.targets.android_target import AndroidTarget
from pants.backend.jvm.targets.import_jars_mixin import ImportJarsMixin
from pants.base.exceptions import TargetDefinitionException
from pants.base.payload import Payload
from pants.base.payload_field import PrimitiveField


class AndroidLibrary(ImportJarsMixin, AndroidTarget):
  """Android library projects that access Android API or Android resources.

   The library project can be either a jar or aar file. Jar files must define an manifest
   field for the AndroidManifest.xml and optionally have an AndroidResources target
   dependency. AndroidLibrary targets that are aar files have their manifest and
   resources contained within the binary file."""
  # TODO(mateor) Perhaps add a BUILD file attribute to force archive type: one of (jar, aar).

  def __init__(self, payload=None, manifest=None,
               libraries=None, include_patterns=None, exclude_patterns=None, **kwargs):
    """
    :param list imports: List of addresses of `jar_library <#jar_library>`_
      targets.
    """
    payload = payload or Payload()
    payload.add_fields({
      'library_specs': PrimitiveField(libraries or ())
    })
    self.libraries = libraries
    self.include_patterns = include_patterns or []
    self.exclude_patterns = exclude_patterns or []
    self._manifest = manifest
    self.manifest_path = None
    print("KWARGS: ", kwargs)
    # TODO(BEFORE REVIEW: make 'libraries' just 'library' for android_library targets
    super(AndroidLibrary, self).__init__(payload=payload, **kwargs)


  @property
  def imported_jar_library_specs(self):
    """List of JarLibrary specs to import.

    Required to implement the ImportJarsMixin.
    """
    return self.payload.library_specs

  @property
  def manifest(self):
    if self._manifest is None:
      try:
        self._manifest = AndroidManifestParser.parse_manifest(self.manifest_path)
      except AndroidManifestParser.BadManifestError:
        raise TargetDefinitionException(self, "An android_library BUILD file must declare a "
                                              "manifest if the library is a jar file or else there "
                                              "must be an AndroidManifest.xml contained within the "
                                              "library's .aar file: {}.".format(self))
    return self._manifest

  @property
  def manifest_required(self):
    """Returns False as an AndroidManifest.xml is not required to be declared in the BUILD file."""
    return False
