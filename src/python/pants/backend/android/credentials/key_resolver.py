# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from pants.backend.android.credentials.keystore import Keystore
from pants.base.config import ChainedConfig


_CONFIG_SECTION = 'android-keystore'

class KeyResolver(ChainedConfig):
  """Parse the keystore config files and instantiate Keystore objects with the info."""
  def __init__(self, target):
    #TODO(BEFORE REVIEW) if config is none, default to debug entry in pants.ini?
    # That will allow us to raise an exception if the build definition is release,
    # thereby protecting from putting secret credentials in pants.ini.
    self.configs = [target.keystore_configs]
    super(KeyResolver, self).__init__(self.configs)

  @classmethod
  def resolve(cls, target):
    """Parse a target's keystore_config_file and return a list of Keystore objects."""
    # This needs to take the target's keystores and pull them from the keystore.configs.

    #TODO: shorthand for homedir in BUILD files? They are supposed to be local only so...
        # ini answer: pants_supportdir
    # I would like to have per-target config files as an option.
    # as of now, the only answer is to put the config address in pants.ini exclusively.

    parser = cls.load(target.keystore_configs)
    #print("sections: {0}".format(parser.__))

    print(parser.sources())
    key_defs = []
    def create_key(key_name):

      print("Location: {0}".format(parser.get(key, 'keystore_location')))

    for key in target.keystore_names:
      create_key(key)


    print(key_defs)
    keys = []
    for definition in key_defs:
      key_defs[definition]

