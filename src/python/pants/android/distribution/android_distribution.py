# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
#TODO Reinstate log stuff
#from twitter.common import log

class AndroidDistribution(object):
    """
    Placeholder class for finding ANDROID_SDK_HOME, until a decision on whether/how
    to bootstrap tools is reached.

    If we use the local Android SDK, it might make sense to refactor 'distribution'
    out of the "java" package and subclass handling for Android SDK along with the JDK/JRE.

    If we keep android distribution separate, then this will be fleshed out and error-catched.
    """
    #TODO: Refactor cloned code from Distribution, in some way that is agreeable to upstream.


    class Error(Exception):
        """Indicates an invalid java distribution."""

    _ANDROID_SDK = {}

    @classmethod
    def cached(cls):
        key = 'sdk'
        dist = cls._ANDROID_SDK.get(key)
        if not dist:
            dist = cls.locate()
        cls._ANDROID_SDK = dist
        return dist


    @classmethod
    def locate(cls):
        def sdk_path(sdk_env_var):
            sdk = os.environ.get(sdk_env_var)
            return os.path.abspath(sdk) if sdk else None

        def search_path():
            yield sdk_path('ANDROID_HOME')
            yield sdk_path('ANDROID_SDK_HOME')
            yield sdk_path('ANDROID_SDK')

        for path in filter(None, search_path()):
            try:
                dist = cls(path)
                dist.validate()
                #log.debug('Located %s' % ('SDK'))
                return dist
            except (ValueError, cls.Error):
                pass
        raise cls.Error('Failed to locate and set %s' % ('SDK'))


    #create a distribution (aapt, all the rest of tools as needed)
    def __init__(self, sdk_path, minimum_sdk=None, target_sdk=None):
        if not os.path.isdir(sdk_path):
            raise ValueError('The specified android sdk path is invalid: %s' % sdk_path)
        self._sdk_path = sdk_path
        # Implement these min/target sdks as I come to it. I need a manifest parser first.
        self._minimum_sdk = minimum_sdk
        self._target_sdk = target_sdk
        self._validated_binaries = {}



    def validate(self):
        if self._validated_binaries:
            return
        try:
            self._validated_executable(self._android_tool())  # Calling purely for the check and cache side effects
        except self.Error:
            raise

    def _validated_executable(self, name):
        exe = self._validated_binaries.get(name)
        if not exe:
            exe = self._validate_executable(name)
            self._validated_binaries[name] = exe
        return exe

    def _validate_executable(self, name):
        exe = os.path.join(self._sdk_path, name)
        #TODO remove Debug
        print(exe)
        if not self._is_executable(exe):
            raise self.Error('Failed to locate the %s executable, %s does not appear to be a'
                             ' valid %s' % (name, self, 'Android SDK'))
        return exe

    @staticmethod
    def _is_executable(path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def _aapt_tool(self):
        pass

    def _android_tool(self):
        return (os.path.join('tools','android'))

