# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from pants.base.config import Config, SingleFileConfig
from pants.backend.android.credentials.keystore import Keystore


class KeyResolver(object):
  """Parse the keystore config files and instantiate Keystore objects with the info."""

  @classmethod
  def resolve(cls, config_file):
    """Parse a target's keystore_config_file and return a list of Keystore objects."""
    # This needs to take the target's keystores and pull them from the keystore.configs.

    config = Config.create_parser()
    with open(config_file, 'r') as keystore_config:
      config.readfp(keystore_config)
    parser = SingleFileConfig(config_file, config)
    key_names = config.sections()
    # keys will be mapped to key_name:Keystore object
    keys = {}

    def create_key(key_name):
      keystore = Keystore(keystore_name=key_name,
                          build_type=parser.get_required(key_name, 'build_type'),
                          keystore_location=parser.get_required(key_name, 'keystore_location'),
                          keystore_alias=parser.get_required(key_name, 'keystore_alias'),
                          keystore_password=parser.get_required(key_name, 'keystore_password'),
                          key_password=parser.get_required(key_name, 'key_password'))
      return keystore

      #TODO (BEFORE REVIEW) Errorcatch bad values (especially build_type)
      #TODO (BEFORE REVIEW) Fix name of TestAndroidDistributionTest
        # No, I think that should go in Keystore.

    for name in key_names:
      keys[name] = (create_key(name))
    return keys


