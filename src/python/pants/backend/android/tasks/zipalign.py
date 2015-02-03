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
  """Task to run zipalign, an archive alignment tool."""

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

     :param string package: Location of a signed apk product from the SignApk task.
     :param AndroidBinary target: Target to be zipaligned.
     """
    # Glossary of used zipalign flags:
    #   : '-f' is to force overwrite of existing outfile.
    #   :  '4' is the mandated byte alignment ordering. If not 4, zipalign essentially does nothing.
    #   :   Last two args are infile, outfile.
    args = [self.zipalign_binary(target)]
    args.extend(['-f', '4', ])
    args.extend([package, os.path.join(self.zipalign_out(target),
                                       '{0}.signed.apk'.format(target.app_name))])
    logger.debug('Executing: {0}'.format(' '.join(args)))
    return args

  def execute(self):
    targets = self.context.targets(self.is_zipaligntarget)
    for target in targets:

      def get_products_path(target):
        """Get path of target's apks that are signed with release keystores with SignApk."""
        apks = self.context.products.get('release_apk')
        if apks.get(target):
          # This allows for multiple apks but we expect only one per target.
          for tgts, products in apks.get(target).items():
            for prod in products:
              yield os.path.join(tgts, prod)

      packages = list(get_products_path(target))
      for package in packages:
        safe_mkdir(self.zipalign_out(target))
        args = self.render_args(package, target)
        with self.context.new_workunit(name='zipalign', labels=[WorkUnit.MULTITOOL]) as workunit:
          returncode = subprocess.call(args, stdout=workunit.output('stdout'),
                                       stderr=workunit.output('stderr'))
          if returncode:
            raise TaskError('The zipalign process exited non-zero: {0}'
                            .format(returncode))

  def zipalign_binary(self, target):
    """Return the appropriate zipalign binary.

    :param string target_sdk: The Android SDK version number of the target (e.g. '18').
    """
    zipalign_binary = os.path.join('build-tools', target.build_tools_version, 'zipalign')
    return self._android_dist.register_android_tool(zipalign_binary)

  def zipalign_out(self, target):
    """Compute the outdir for the zipalign task."""
    return os.path.join(self._distdir, target.name)
