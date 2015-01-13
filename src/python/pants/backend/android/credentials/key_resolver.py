# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

try:
  import ConfigParser
except ImportError:
  import configparser as ConfigParser

from pants.base.config import Config, SingleFileConfig
from pants.backend.android.credentials.keystore import Keystore


_CONFIG_SECTION = 'android-keystore'

class KeyResolver(object):
  """Parse the keystore config files and instantiate Keystore objects with the info."""
  #def __init__(self, target):
    #TODO(BEFORE REVIEW) if config is none, default to debug entry in pants.ini?
    # That will allow us to raise an exception if the build definition is release,
    # thereby protecting from putting secret credentials in pants.ini.
    #self.configs = [target.keystore_configs]

  @classmethod
  def resolve(cls, config_file):
    """Parse a target's keystore_config_file and return a list of Keystore objects."""
    # This needs to take the target's keystores and pull them from the keystore.configs.

    #TODO: shorthand for homedir in BUILD files? They are supposed to be local only so...
        # ini answer: pants_supportdir
    # I would like to have per-target config files as an option.
    # as of now, the only answer is to put the config address in pants.ini exclusively.

    # I would like to allow a shorthand, where if 'keystore_names' is None or not defined
    # in the target's BUILD, that would mean that pants would just use all definition in the
    # keystore_config. If this patch gets traction, I will then put them time into that.

    # For now, 'keystore_names' is required.
    config = Config.create_parser()
    with open(config_file, 'r') as keystore_config:
      config.readfp(keystore_config)
    parser = SingleFileConfig(config_file, config)
    key_names = config.sections()
    keys = {}

    def create_key(key_name):
      keystore = Keystore(build_type=parser.get_required(key_name, 'build_type'),
                          keystore_location=parser.get_required(key_name, 'keystore_location'),
                          keystore_alias=parser.get_required(key_name, 'keystore_alias'),
                          keystore_password=parser.get_required(key_name, 'keystore_password'),
                          key_password=parser.get_required(key_name, 'key_password'))
      return keystore

      #TODO (BEFORE REVIEW) Errorcatch bad values (especially build_type)

      print("Location: {0}".format(parser.get_required(key, 'keystore_location')))

    for name in key_names:
      print(name)
      print(parser.get_required(name, 'keystore_location'))
      keys[name] = (create_key(name))
    return keys


