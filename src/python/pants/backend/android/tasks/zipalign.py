# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import logging
import os
import subprocess

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.tasks.android_task import AndroidTask
from pants.base.exceptions import TaskError
from pants.base.workunit import WorkUnit
from pants.util.dirutil import safe_mkdir


logger = logging.getLogger(__name__)


class Zipalign(AndroidTask):
  """Task to run zipalign, which byte-orders signed apks."""

  @classmethod
  def prepare(cls, options, round_manager):
    super(Zipalign, cls).prepare(options, round_manager)
    # Zipalign no-ops on 'debug_apk' but requires both to bundle their tasks into 'binary' goal.
    round_manager.require_data('release_apk')
    round_manager.require_data('debug_apk')

  @staticmethod
  def is_zipaligntarget(target):
    return isinstance(target, AndroidBinary)

  def __init__(self, *args, **kwargs):
    super(Zipalign, self).__init__(*args, **kwargs)
    self._android_dist = self.android_sdk
    self._distdir = self.get_options().pants_distdir

  def render_args(self, package, target):
    """Create arg list for the jarsigner process.

     :param AndroidBinary target: Target to be zipaligned.
     :param string package: Location of the signed apk product from the SignApk task.
     """
    # Glossary of used zipalign flags:
    #   : '-f' is to force overwrite of existing outfile.

    args = [self.zipalign_binary(target)]
    args.extend(['-f', '4', package, os.path.join(self.zipalign_out(target),
                                             '{0}.signed.apk'.format(target.app_name))])
    logger.debug('Executing: {0}'.format(' '.join(args)))
    return args

  # TODO (BEFORE REVIEW) Why isn't the failure coming up?

  def execute(self):
    targets = self.context.targets(self.is_zipaligntarget)
    for target in targets:
      signed_apks = self.context.products.get('release_apk')
      print("Release builds: {0}".format(signed_apks))

      # I reuse this function to get the path of a product from an earlier task.
      # I see the jar pipeline does something similar.
      #  any interest in bringing something like it up to Products?
      # something like Product.get_product(typename, target)
      # Or is there already something like this I missed?

      def get_products_path(target):
        """Get path of target's signed apks as created by SIgnApk."""
        unsigned_apks = self.context.products.get('release_apk')
        if unsigned_apks.get(target):
          # This allows for multiple apks but we expect only one per target.
          for tgts, products in unsigned_apks.get(target).items():
            for prod in products:
              yield os.path.join(tgts, prod)

      packages = list(get_products_path(target))
      print("PACKAGES: {0}".format(packages))
      for package in packages:
        safe_mkdir(self.zipalign_out(target))
        args = self.render_args(package, target)
        print( "ARGS: {0}".format(args))
        with self.context.new_workunit(name='zipalign',
                                       labels=[WorkUnit.MULTITOOL]) as workunit:
          returncode = subprocess.call(args, stdout=workunit.output('stdout'),
                                       stderr=workunit.output('stderr'))
          if returncode:
            raise TaskError('The zipalign process exited non-zero: {0}'
                            .format(returncode))
          pass
    #TODO(BEFORE REVIEW: MOve the SignAPk products away from dist.) Zipalign is where we wil release.

  def zipalign_binary(self, target):
    """Return the appropriate android.jar.

    :param string target_sdk: The Android SDK version number of the target (e.g. '18').
    """
    zipalign_binary = os.path.join('build-tools', target.build_tools_version, 'zipalign')
    return self._android_dist.register_android_tool(zipalign_binary)

  def zipalign_out(self, target):
    """Compute the outdir for a target."""
    return os.path.join(self._distdir, target.name)