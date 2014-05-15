# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from twitter.common.collections import OrderedSet
from twitter.common.dirutil import safe_mkdir

from pants.base.build_environment import get_buildroot
from pants.fs import archive
from pants.java.jar import Manifest
from pants.targets.jvm_binary import JvmApp, JvmBinary
from pants.tasks.jvm_binary_task import JvmBinaryTask


class BundleCreate(JvmBinaryTask):

  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag('deployjar'), mkflag('deployjar', negate=True),
                            dest='bundle_create_deployjar', default=False,
                            action='callback', callback=mkflag.set_bool,
                            help="[%default] Expand 3rdparty jars into loose classfiles in the "
                                 "bundle's classes dir. If unset, 3rdparty jars go into a libs dir.")

    archive_flag = mkflag('archive')
    option_group.add_option(archive_flag, dest='bundle_create_archive',
                            type='choice', choices=list(archive.TYPE_NAMES),
                            help='[%%default] Create an archive from the bundle. '
                                 'Choose from %s' % sorted(archive.TYPE_NAMES))

    option_group.add_option(mkflag('archive-prefix'), mkflag('archive-prefix', negate=True),
                            dest='bundle_create_prefix', default=False,
                            action='callback', callback=mkflag.set_bool,
                            help='[%%default] Used in conjunction with %s this packs the archive '
                                 'with its basename as the path prefix.' % archive_flag)

  def __init__(self, context, workdir):
    super(BundleCreate, self).__init__(context, workdir)
    self._outdir = context.config.getdefault('pants_distdir')
    self._prefix = context.options.bundle_create_prefix
    self._archiver_type = context.options.bundle_create_archive
    self._create_deployjar = context.options.bundle_create_deployjar

  class App(object):
    """A uniform interface to an app."""

    @staticmethod
    def is_app(target):
      return isinstance(target, (JvmApp, JvmBinary))

    def __init__(self, target):
      assert self.is_app(target), '%s is not a valid app target' % target

      self.binary = target if isinstance(target, JvmBinary) else target.binary
      self.bundles = [] if isinstance(target, JvmBinary) else target.bundles
      self.basename = target.basename

  def execute(self, _):
    archiver = archive.archiver(self._archiver_type) if self._archiver_type else None
    for target in self.context.target_roots:
      for app in map(self.App, filter(self.App.is_app, target.resolve())):
        basedir = self.bundle(app)
        if archiver:
          archivepath = archiver.create(
            basedir,
            self._outdir,
            app.basename,
            prefix=app.basename if self._prefix else None
          )
          self.context.log.info('created %s' % os.path.relpath(archivepath, get_buildroot()))

  def bundle(self, app):
    """Create a self-contained application bundle.

    The bundle will contain the target classes, dependencies and resources.
    """
    assert(isinstance(app, BundleCreate.App))

    bundle_dir = os.path.join(self._outdir, '%s-bundle' % app.basename)
    self.context.log.info('creating %s' % os.path.relpath(bundle_dir, get_buildroot()))

    safe_mkdir(bundle_dir, clean=True)

    classpath = OrderedSet()
    # If creating a deployjar, we add the external dependencies to the bundle as
    # loose classes, and have no classpath. Otherwise we add the external dependencies
    # to the bundle as jars in a libs directory.
    if not self._create_deployjar:
      lib_dir = os.path.join(bundle_dir, 'libs')
      os.mkdir(lib_dir)

      for basedir, external_jar in self.list_jar_dependencies(app.binary):
        path = os.path.join(basedir, external_jar)
        os.symlink(path, os.path.join(lib_dir, external_jar))
        classpath.add(external_jar)

    bundle_jar = os.path.join(bundle_dir, '%s.jar' % app.binary.basename)

    with self.loose_classfiles_jar(app.binary, bundle_jar,
                                   with_external_deps=self._create_deployjar) as jar:
      manifest = self.create_main_manifest(app.binary)
      if classpath:
        manifest.addentry(Manifest.CLASS_PATH,
                          ' '.join(os.path.join('libs', jar) for jar in classpath))
      jar.writestr(Manifest.PATH, manifest.contents())

    for bundle in app.bundles:
      for path, relpath in bundle.filemap.items():
        bundle_path = os.path.join(bundle_dir, relpath)
        safe_mkdir(os.path.dirname(bundle_path))
        os.symlink(path, bundle_path)

    return bundle_dir
