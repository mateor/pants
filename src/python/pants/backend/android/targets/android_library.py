# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import logging

from pants.backend.android.targets.android_target import AndroidTarget
from pants.backend.jvm.targets.import_jars_mixin import ImportJarsMixin
from pants.base.payload import Payload
from pants.base.payload_field import PrimitiveField


logger = logging.getLogger(__name__)


class AndroidLibrary(ImportJarsMixin, AndroidTarget):
  """Generates a stub Java library from protobuf IDL files."""

  def __init__(self, payload=None, imports=None, **kwargs):
    """
    :param list imports: List of addresses of `jar_library <#jar_library>`_
      targets which contain .proto definitions.
    """
    payload = payload or Payload()
    # TODO(Eric Ayers): The target needs to incorporate the settings of --gen-protoc-version
    # and --gen-protoc-plugins into the fingerprint.  Consider adding a custom FingeprintStrategy
    # into ProtobufGen to get it.
    payload.add_fields({
      'import_specs': PrimitiveField(imports or ())
    })
    super(AndroidLibrary, self).__init__(payload=payload, **kwargs)

  @property
  def imported_jar_library_specs(self):
    """List of JarLibrary specs to import.

    Required to implement the ImportJarsMixin.
    """
    return self.payload.import_specs
