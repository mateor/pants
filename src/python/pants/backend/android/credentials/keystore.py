# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)


class Keystore(object):
  """Represents a keystore configuration"""

  def __init__(self,
               keystore_name=None,
               build_type=None,
               keystore_location=None,
               keystore_alias=None,
               keystore_password=None,
               key_password=None,
               **kwargs):
    """
    :param string build_type: What type of package the keystore signs. Either 'debug' or 'release'.
    :param string source: path/to/keystore
    :param string keystore_alias: The alias of this keystore.
    :param string keystore_password: The password for the keystore.
    :param string key_password: The password for the key.
    """

    self.keystore_name=keystore_name
    # Error catching for these fields can be done in the KeyResolver
    self.build_type = build_type
    self.keystore_location = keystore_location
    self.keystore_alias = keystore_alias
    self.keystore_password = keystore_password
    self.key_password = key_password
