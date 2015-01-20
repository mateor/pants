# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from pants.base.config import Config, SingleFileConfig


class KeystoreResolver(object):
  """Read a keystore config.ini file and instantiate Keystore objects with the info."""

  @classmethod
  def resolve(cls, config_file):
    """Parse a target's keystore_config_file and return a list of Keystore objects."""
    #TODO (BEFORE REVIEW) Check to be robust against no config file. (In SIgnApk)
      # TODO(BEFORE REVIEW) write test to conifrm thism=.
    config = Config.create_parser()
    with open(config_file, 'r') as keystore_config:
      config.readfp(keystore_config)
    parser = SingleFileConfig(config_file, config)
    key_names = config.sections()
    keys = {}

    def create_key(key_name):
      keystore = Keystore(keystore_name=key_name,
                          build_type=parser.get_required(key_name, 'build_type'),
                          keystore_location=parser.get_required(key_name, 'keystore_location'),
                          keystore_alias=parser.get_required(key_name, 'keystore_alias'),
                          keystore_password=parser.get_required(key_name, 'keystore_password'),
                          key_password=parser.get_required(key_name, 'key_password'))
      return keystore

      #TODO (BEFORE REVIEW) Turn the KeyResolver into a factory, That is the proper design pattern for this.
      #TODO (BEFORE REVIEW) Fix name of TestAndroidDistributionTest

    for name in key_names:
      keys[name] = (create_key(name))
    return keys


class Keystore(object):
  """Represents a keystore configuration."""

  def __init__(self,
               build_type=None,
               keystore_name=None,
               keystore_location=None,
               keystore_alias=None,
               keystore_password=None,
               key_password=None,
               **kwargs):
    """
    :param string name: Name of keystore. This is the [section] of the .ini config file.
    :param string build_type: What type of the keystore. One of (debug, release).
    :param string keystore_location: path/to/keystore.
    :param string keystore_alias: The alias of this keystore.
    :param string keystore_password: The password for the keystore.
    :param string key_password: The password for the key.
    """

    self._type = None
    self._build_type = build_type

    # TODO (BEFORE REVIEW) write test to confirm
    self.keystore_name=keystore_name
    # The os call is robust against None b/c it was validated in KeyResolver with get_required().
    self.keystore_location = os.path.expandvars(keystore_location)
    self.keystore_alias = keystore_alias
    self.keystore_password = keystore_password
    self.key_password = key_password

    @property
    def build_type(self):
      if self._type is None:
        if self._build_type.lower() not in ('release', 'debug'):
          raise ValueError(self, "The 'build_type' must be one of (debug, release)"
                                 " instead of: '{0}'.".format(build_type))
      return self._type