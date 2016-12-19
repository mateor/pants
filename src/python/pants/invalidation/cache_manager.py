# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
import shutil
import sys

from pants.build_graph.build_graph import sort_targets
from pants.build_graph.target import Target
from pants.invalidation.build_invalidator import BuildInvalidator, CacheKeyGenerator
from pants.util.dirutil import relative_symlink, safe_mkdir, safe_rmtree
from pants.util.memo import memoized_property


class VersionedTarget(object):
  """This class represents a singleton VersionedTargetSet, and has links to VersionedTargets that
  the wrapped target depends on (after having resolved through any "alias" targets).

  :API: public
  """

  class IllegalResultsDir(Exception):
    """Indicate a problem interacting with a versioned target results directory."""

  _STABLE_DIR_NAME = 'current'

  def __init__(self, cache_manager, targets, cache_key):
    """
    :API: public
    """
    self.targets = targets
    self.target = self.targets[0]
    self.versioned_targets = [self]
    if not isinstance(self.target, Target):
      raise ValueError("The target {} must be an instance of Target but is not.".format(self.target.id))
    self.id = self.target.id

    self.cache_key = cache_key
    self._cache_manager = cache_manager
    self.previous_cache_key = cache_manager.previous_key(self.cache_key)

    # NOTE: VTs can be forced invalid, which currently involves resetting 'self.valid' to False.
    self.valid = self.previous_cache_key == self.cache_key
    if cache_manager.invalidation_report:
      cache_manager.invalidation_report.add_vts(cache_manager, self.targets, self.cache_key, self.valid, phase='init')

  @memoized_property
  def root_dir(self):
    return self._cache_manager.root_dir

  def _calculate_results_path(self, key, stable=False):
    """Return a results directory path for the given key.

    :param key: A CacheKey to generate an id for.
    :param stable: True to use a stable subdirectory, false to use a portion of the cache key to
      generate a path unique to the key.
    """
    # TODO: Shorten cache_key hashes in general?
    task_hash = CacheKeyGenerator.hash_value(self._cache_manager.task_version)
    dir_name = self._STABLE_DIR_NAME if stable else CacheKeyGenerator.hash_value(key.hash)
    return os.path.join(
        self.root_dir,
        task_hash,
        key.id,
        dir_name,
    )

  @memoized_property
  def _stable_results_path(self):
    # Return the path for the stable results_dir without relying on it existing.
    return self._calculate_results_path(self.cache_key, stable=True)

  @memoized_property
  def _unique_results_path(self):
    # Return the path for the namespaced unique_results_dir without relying on it existing.
    return self._calculate_results_path(self.cache_key)

  @memoized_property
  def _previous_results_path(self):
    # File path that would hold the previous VT.unique_results_dir. This can be None if no previous_cache_key is found.
    return self._calculate_results_path(self.previous_cache_key) if self.previous_cache_key else None

  @memoized_property
  def results_dir(self):
    """Return file path that represents the stable output location for these targets.

    The results_dir is represented by a stable symlink to the unique_results_dir: consumers
    should generally prefer to access this stable directory.
    """
    if not os.path.isdir(self._stable_results_path):
      raise ValueError('No results_dir was created for {}'.format(self))
    return self._stable_results_path

  # TODO(mateo): Deprecation cycle for the 'current_results_dir'?
  @memoized_property
  def unique_results_dir(self):
    """Return unique file path to use as an output directory by these targets.

    The unique_results_dir is derived from the VTS cache_key(s). The results_dir is a symlink to the unique_results_dir:
    consumers should generally prefer that stable location as referenced by results_dir.
    """
    if not os.path.isdir(self._unique_results_path):
      raise ValueError('No results_dir was created for {}'.format(self))
    return self._unique_results_path

  @memoized_property
  def previous_results_dir(self):
    """Return file path that corresponds to the unique_results_dir of the most recent build of these targets.

    The previous_results_dir differs from results_dir and unique_results_dir since it is not required in order for
    the task to function, even if the task enables incremental results.
    Returns None if directory does not exist.
    """
    # Only used by tasks that enable incremental results.
    # TODO: Exposing old results is a bit of an abstraction leak, because ill-behaved Tasks could mutate them.
    if self._previous_results_path and os.path.isdir(self._previous_results_path):
      return self._previous_results_path
    return None

  def _ensure_legal(self):
    """Return True as long as the state does not break any internal contracts."""
    # Do our best to provide complete feedback, it's easy to imagine the frustration of flipping between error states.
    if self._has_results_dir():
      errors = ''
      if not os.path.islink(self.results_dir):
        errors += '\nThe results_dir is no longer a symlink:\n\t* {}'.format(self.results_dir)
      if not os.path.isdir(self.unique_results_dir):
        errors += '\nThe unique_results_dir directory was not found\n\t* {}'.format(self.unique_results_dir)
      if errors:
        raise self.IllegalResultsDir(
          '\nThe results_dirs should not be manually cleaned or recreated by tasks.\n{}'.format(errors)
        )
    return True

  def _has_results_dir(self):
    return os.path.lexists(self._stable_results_path)

  def live_dirs(self):
    """Return directories that must be preserved in order for this VersionedTarget to function."""
    # Returning paths instead of verified dirs since the only current caller subsumes errors in a background process.
    # Not including previous_dir, since when this is called the contents of the previous dir have been copied as needed.
    live = []
    if self._has_results_dir():
      live.append(self._stable_results_path)
      live.append(self._unique_results_path)
    return live

  def create_results_dir(self):
    """Ensure that the empty results directory and a stable symlink exist for these versioned targets."""
    if not self.valid:
      # Clean the workspace for invalid vts.
      safe_mkdir(self._unique_results_path, clean=True)
      relative_symlink(self._unique_results_path, self._stable_results_path)
    self._ensure_legal()

  def copy_previous_results(self):
    """Use the latest valid results_dir as the starting contents of the current results_dir.

    Should be called after the cache is checked, since previous_results are not useful if there is a cached artifact.
    """
    if self.previous_results_dir:
      safe_rmtree(self.unique_results_dir)
      shutil.copytree(self.previous_results_dir, self.unique_results_dir)

  def force_invalidate(self):
    # Note: This method isn't exposted as Public because the api is not yet
    # finalized, however it is currently used by Square for plugins.  There is
    # an open OSS issue to finalize this API.  Please take care when changing
    # until https://github.com/pantsbuild/pants/issues/2532 is resolved.
    self._cache_manager.force_invalidate(self)

  def update(self):
    self._ensure_legal()
    self._cache_manager.update(self)

  def __repr__(self):
    return 'VT({}, {})'.format(self.target.id, 'valid' if self.valid else 'invalid')


class VersionedTargetSet(VersionedTarget):
  """Represents a list of targets, a corresponding CacheKey, and a flag determining whether the
  list of targets is currently valid.

  When invalidating a single target, this can be used to represent that target as a singleton.
  When checking the artifact cache, this can also be used to represent a list of targets that are
  built together into a single artifact.
  """

  @staticmethod
  def from_versioned_targets(versioned_targets):
    """
    :API: public
    """
    # This should be protected against being passed an empty list.

    # Quick sanity check; all the versioned targets should have the same cache manager.
    # TODO(ryan): the way VersionedTargets store their own links to a single CacheManager instance
    # feels hacky; see if there's a cleaner way for callers to handle awareness of the CacheManager.
    first_target = versioned_targets[0]
    cache_manager = first_target._cache_manager
    for versioned_target in versioned_targets:
      if versioned_target._cache_manager != cache_manager:
        raise ValueError(
          "Attempting to combine versioned targets {} and {} with different CacheManager instances: {} and {}"
          .format(first_target, versioned_target, cache_manager, versioned_target._cache_manager)
        )
    return VersionedTargetSet(cache_manager, versioned_targets)

  @staticmethod
  def from_invalidation_check(invalidation_check):
    return VersionedTargetSet(invalidation_check.cache_manager, invalidation_check.all_vts)

  def __init__(self, cache_manager, versioned_targets):
    self.versioned_targets = versioned_targets
    self.targets = [vt.target for vt in versioned_targets]

    self.cache_key = CacheKeyGenerator.combine_cache_keys([vt.cache_key for vt in versioned_targets])
    super(VersionedTargetSet, self).__init__(cache_manager, self.targets, self.cache_key)

  def __repr__(self):
    return 'VTS({}, {})'.format(','.join(target.address.spec for target in self.targets),
                                'valid' if self.valid else 'invalid')


class InvalidationCheck(object):
  """The result of calling check() on a CacheManager.

  The vts members are lists of VersionedTargets.  Sorting of the targets depends
  on how you order the InvalidationCheck from the InvalidationCacheManager.

  Tasks may need to perform no, some or all operations on either of those, depending on how they
  are implemented.
  """

  def __init__(self, all_vts, invalid_vts, cache_manager=None, as_target_set=False):
    """
    :API: public
    """

    # All the targets, valid and invalid.
    self.all_vts = all_vts
    # Just the invalid targets.
    self.invalid_vts = invalid_vts

    # Reference to the InvalidationCacheManager that owns these vts.
    self.cache_manager = cache_manager or all_vts[0]._cache_manager if all_vts else None
    self.as_target_set = as_target_set


class InvalidationCacheManager(object):
  """Manages cache checks, updates and invalidation keeping track of basic change
  and invalidation statistics.
  Note that this is distinct from the ArtifactCache concept, and should probably be renamed.
  """

  class CacheValidationError(Exception):
    """Indicates a problem accessing the cache."""

  def __init__(self,
               cache_key_generator,
               build_invalidator_dir,
               invalidate_dependents,
               as_target_set=False,
               root_dir=None,
               fingerprint_strategy=None,
               invalidation_report=None,
               task_name=None,
               task_version=None,
               artifact_write_callback=lambda _: None):
    """
    :API: public
    """
    # NOTE(mateo): IMHO, most of these params should just be removed in favor of the task instance.
    # The API would become much simpler and the only levers used by tasks are invalidate_deps and fp_strategy.
    # Every other param is a task attribute/option/callback.
    self._cache_key_generator = cache_key_generator
    self.task_name = task_name or 'UNKNOWN'
    self.task_version = task_version or 'Unknown_0'

    self.root_dir = root_dir
    self._invalidate_dependents = invalidate_dependents
    self.as_target_set = as_target_set

    self._invalidator = BuildInvalidator(build_invalidator_dir)
    self._fingerprint_strategy = fingerprint_strategy
    self._artifact_write_callback = artifact_write_callback
    self.invalidation_report = invalidation_report

  def update(self, vts):
    """Mark a changed or invalidated VersionedTargetSet as successfully processed."""
    for vt in vts.versioned_targets:
      if not vt.valid:
        self._invalidator.update(vt.cache_key)
        vt.valid = True
        self._artifact_write_callback(vt)
    if not vts.valid:
      self._invalidator.update(vts.cache_key)
      vts.valid = True
      self._artifact_write_callback(vts)

  def force_invalidate(self, vts):
    """Force invalidation of a VersionedTargetSet."""
    for vt in vts.versioned_targets:
      self._invalidator.force_invalidate(vt.cache_key)
      vt.valid = False
    self._invalidator.force_invalidate(vts.cache_key)
    vts.valid = False

  def check(self,
            targets,
            topological_order=False):
    """Checks whether each of the targets has changed and invalidates it if so.

    Returns a list of VersionedTargetSet objects (either valid or invalid). The returned sets
    'cover' the input targets, with one caveat: if the FingerprintStrategy
    opted out of fingerprinting a target because it doesn't contribute to invalidation, then that
    target will be excluded from all_vts and invalid_vts.

    Callers can inspect these vts and rebuild the invalid ones, for example.
    """
    all_vts = self.wrap_targets(targets, topological_order=topological_order)
    invalid_vts = filter(lambda vt: not vt.valid, all_vts)
    return InvalidationCheck(all_vts, invalid_vts, cache_manager=self, as_target_set=self.as_target_set)

  def wrap_targets(self, targets, topological_order=False):
    """Wrap targets and their computed cache keys in VersionedTargets.

    If the FingerprintStrategy opted out of providing a fingerprint for a target, that target will not
    have an associated VersionedTarget returned.

    Returns a list of VersionedTargets, each representing one input target.
    """
    def vt_iter():
      if topological_order:
        target_set = set(targets)
        sorted_targets = [t for t in reversed(sort_targets(targets)) if t in target_set]
      else:
        sorted_targets = sorted(targets)
      for target in sorted_targets:
        target_key = self._key_for(target)
        if target_key is not None:
          yield VersionedTarget(self, [target], target_key)
    return list(vt_iter())

  def previous_key(self, cache_key):
    return self._invalidator.previous_key(cache_key)

  def _key_for(self, target):
    try:
      return self._cache_key_generator.key_for_target(target,
                                                      transitive=self._invalidate_dependents,
                                                      fingerprint_strategy=self._fingerprint_strategy)
    except Exception as e:
      # This is a catch-all for problems we haven't caught up with and given a better diagnostic.
      # TODO(Eric Ayers): If you see this exception, add a fix to catch the problem earlier.
      exc_info = sys.exc_info()
      new_exception = self.CacheValidationError("Problem validating target {} in {}: {}"
                                                .format(target.id, target.address.spec_path, e))

      raise self.CacheValidationError, new_exception, exc_info[2]
