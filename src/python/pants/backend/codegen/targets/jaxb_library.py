# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from hashlib import sha1
from types import GeneratorType
import sys

from twitter.common.collections import OrderedSet

from pants.backend.jvm.targets.jvm_target import JvmTarget
from pants.base.build_environment import get_buildroot
from pants.base.build_manual import manual
from pants.base.payload import hash_sources, Payload, SourcesMixin


# TODO(Garrett Malmquist): Create an ExtensiblePayloads class which all Payloads can extend from in
# a way that easily allows extension via normal inheritance, rather than having to copypasta code
# every time a single variable needs to be added. For example particular, JvmTargetPayload would
# inherit from ExtensiblePayload, and JaxbPayload would inherit from JvmTargetPayload. It might also
# be a good idea to just put this code in the Payload class itself, so that any payload could derive
# from any other payload without excessive copypasta. A change like this could reduce JaxbPayload to
# about 4 lines of code.
class JaxbPayload(SourcesMixin, Payload):
  def __init__(self,
               sources_rel_path=None,
               sources=None,
               provides=None,
               excludes=None,
               configurations=None,
               package=None):
    self.sources_rel_path = sources_rel_path
    self.sources = list(sources or [])
    self.provides = provides
    self.excludes = OrderedSet(excludes)
    self.configurations = OrderedSet(configurations)
    self.package = package

  def __hash__(self):
    return hash((frozenset(self.sources), self.provides, self.excludes, self.configurations, self.package))

  def invalidation_hash(self):
    hasher = sha1()
    sources_hash = hash_sources(get_buildroot(), self.sources_rel_path, self.sources)
    hasher.update(sources_hash)
    if self.provides:
      hasher.update(bytes(hash(self.provides)))
    for exclude in sorted(self.excludes):
      hasher.update(bytes(hash(exclude)))
    for config in sorted(self.configurations):
      hasher.update(config)
    if self.package:
      hasher.update(bytes(self.package))
    return hasher.hexdigest()

@manual.builddict(tags=["java"])
class JaxbLibrary(JvmTarget):
  """Generates a stub Java library from jaxb xsd files."""

  def __init__(self,
               package=None,
               language='java',
               **kwargs):
    """Initialize the JaxbLibrary target, currently with a lot of copypasta for the payload.

    :param package: java package (com.company.package) in which to generate the output java files.
    If left unspecified, pants will attempt to guess it from the file path leading to the schema
    (xsd) file. This will only be accurate if the .xsd file is in the format
    .../com/company/package/schema.xsd; it is recommended that the package be manually defined in
    the BUILD file for robustness.
    :param language: currently, anything other than 'java' is unsupported (this is the default)
    :param buildflags: currently unused Parameters inherited from JvmTarget.
    :param string name: The name of this target, which combined with this build file defines the
    target :class:`pants.base.address.Address`.
    :param sources: A list of filenames representing the source code this library is compiled from.
    :type sources: ``FileSet`` or list of strings.
    :param dependencies: List of :class:`pants.base.target.Target` instances this target depends on.
    :type dependencies: Other targets that this target depends on.
    :type dependencies: List of target specs.
    :param excludes: One or more :class:`pants.targets.exclude.Exclude` instances to filter this
    target's transitive dependencies against.
    :param configurations: One or more ivy configurations to resolve for this target. This parameter
    is not intended for general use.
    :type configurations: tuple of strings
    """
    super(JaxbLibrary, self).__init__(**kwargs)
    # Create a new payload, ripping properties from the JvmTargetPayload generated by the
    # superclass.
    self.payload = JaxbPayload(sources=self.payload.sources,
                               sources_rel_path=self.payload.sources_rel_path,
                               provides=self.payload.provides,
                               excludes=self.payload.excludes,
                               configurations=self.payload.configurations,
                               package=package)

    self.add_labels('codegen')
    self.add_labels('jaxb')

    if language != 'java':
      raise ValueError('Language "{lang}" not supported for {class_type}'
                       .format(lang=language, class_type=type(self).__name__))

  @property
  def package(self):
    return self.payload.package
