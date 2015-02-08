# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from xml.dom.minidom import parse


class ManifestParser(object):

  class BadManifestError(Exception):
    """Indicates an invalid android manifest."""

  # TODO(mateor) Peel parsing into a ManifestParser class to ensure it's robust against bad input.
  # Parsing as in Android Donut's testrunner:
  # https://github.com/android/platform_development/blob/master/testrunner/android_manifest.py.
  @classmethod
  def get_package_name(cls, target):
    """Return the package name of the Android target."""
    tgt_manifest = parse(target.manifest).getElementsByTagName('manifest')
    if not tgt_manifest or not tgt_manifest[0].getAttribute('package'):
      raise cls.BadManifestError('There is no \'package\' attribute in manifest at: {0!r}'
                                  .format(target.manifest))
    return tgt_manifest[0].getAttribute('package')

  @classmethod
  def get_target_sdk(cls, target):
    """Return a string with the Android package's target SDK."""
    tgt_manifest = parse(target.manifest).getElementsByTagName('uses-sdk')
    if not tgt_manifest or not tgt_manifest[0].getAttribute('android:targetSdkVersion'):
      raise cls.BadManifestError('There is no \'targetSdkVersion\' attribute in manifest at: {0!r}'
                                  .format(target.manifest))
    return tgt_manifest[0].getAttribute('android:targetSdkVersion')

  @classmethod
  def get_app_name(cls, target):
    """Return a string with the application name of the package, return None if not found."""
    tgt_manifest = parse(target.manifest).getElementsByTagName('activity')
    try:
      package_name = tgt_manifest[0].getAttribute('android:name')
      return package_name.split(".")[-1]
    except:
      return None