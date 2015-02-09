# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from xml.dom.minidom import parse


class AndroidManifestParser(object):

  class BadManifestError(Exception):
    """Indicates an invalid android manifest."""

  # Parsing as in Android Donut's testrunner:
  # https://github.com/android/platform_development/blob/master/testrunner/android_manifest.py.

  @classmethod
  def get_package_name(cls, manifest):
    """Return the package name of the Android target."""
    # If manifest tag or package tag is missing, aapt_gen errors and provides that info to stderr.
    # This error catching shouldn't ever hit so the existing checks should be fine.
    manifest_element = parse(manifest).getElementsByTagName('manifest')
    if not manifest_element or not manifest_element[0].getAttribute('package'):
      raise cls.BadManifestError('There is no \'package\' attribute in manifest at: {0}'
                                  .format(manifest))
    return manifest_element[0].getAttribute('package')

  @classmethod
  def get_target_sdk(cls, manifest):
    """Return a string with the Android package's target SDK."""
    # If bad info is passed, the android_distribution class will raise an error
    # since it will not be able to find the associated tool.
    sdk_element = parse(manifest).getElementsByTagName('uses-sdk')
    if not sdk_element or not sdk_element[0].getAttribute('android:targetSdkVersion'):
      raise cls.BadManifestError('There is no \'targetSdkVersion\' attribute in manifest at: {0}'
                                  .format(manifest))
    return sdk_element[0].getAttribute('android:targetSdkVersion')

  @classmethod
  def get_app_name(cls, manifest):
    """Return a string with the application name of the package or return None on failure."""
    # This is used to provide a folder name in dist. Since it has a fallback value any
    # failure returns None. The None case is handled by the consumer.
    try:
      activity_element = parse(manifest).getElementsByTagName('activity')
      package_name = activity_element[0].getAttribute('android:name')
      # The parser returns an empty string if it locates 'android' but cannot find 'name'.
      if package_name not in (None, ''):
        return package_name.split(".")[-1]
      return None
    except:
      return None