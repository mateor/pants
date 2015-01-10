# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from pants.base.exceptions import TargetDefinitionException
from pants.base.target import Target
from pants.base.build_environment import get_buildroot



# This is going to become a subclass of object. Pants isn't building this so it
# shouldn't be a target.

class Keystore(object):
  """Represents a keystore configuration"""

  def __init__(self,
               source=None,
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
    address = kwargs['address']

    # TODO (mateor) if debug location is empty, create a debug.keystore with keytool.

    self.keystore_alias = keystore_alias
    self.keystore_password = keystore_password
    self.key_password = key_password
    