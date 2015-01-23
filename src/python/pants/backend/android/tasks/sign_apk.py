# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import os
import subprocess

from pants.backend.android.targets.android_binary import AndroidBinary
from pants.backend.android.keystore.keystore_resolver import KeystoreResolver
from pants.backend.core.tasks.task import Task
from pants.base.config import Config
from pants.base.exceptions import TaskError
from pants.base.workunit import WorkUnit
from pants.java.distribution.distribution import Distribution
from pants.util.dirutil import safe_mkdir



class SignApkTask(Task):
  """Sign Android packages with jarsigner tool."""

  _CONFIG_SECTION = 'android-keystore-location'

  @classmethod
  def register_options(cls, register):
    super(SignApkTask, cls).register_options(register)
    register('--keystore-config-location',
             help='Location of the .ini file containing keystore definitions.')


  #TODO(BEFORE REVIEW) need to hook into the .pants.d installation and setup the default config file

  #TODO(BEFORE REVIEW) Test passing config from CLI and from ini.

  @classmethod
  def is_signtarget(cls, target):
    return isinstance(target, AndroidBinary)

  @classmethod
  def product_types(cls):
    # TODO(BEFORE REVIEW) verfiy these package names.
    return ['debug_apk', 'release_apk']

  def __init__(self, *args, **kwargs):
    super(SignApkTask, self).__init__(*args, **kwargs)
    self._distdir = self.context.config.getdefault('pants_distdir')
    self._config_file = self.get_options().keystore_config_location
    self._dist = None

  @property
  def config_file(self):
    if self._config_file in (None, ""):
      try:
        self._config_file = self.context.config.get_required(self._CONFIG_SECTION, 'keystore_config_location')
      except Config.ConfigError:
       raise TaskError(self, "To sign .apks an '{0}' option must declare the location of an "
                             ".ini file holding keystore definitions.".format(self._CONFIG_SECTION))
    return self._config_file

  @property
  def distribution(self):
    if self._dist is None:
      # No Java 8 for Android. I am considering max=1.7.0_50. See comment in render_args().
      self._dist = Distribution.cached(maximum_version="1.7.0_99")
    return self._dist


  def prepare(self, round_manager):
    round_manager.require_data('apk')

  def render_args(self, target, unsigned_apk, key):
    """Create arg list for the jarsigner process.

    :param AndroidBinary target: Target to be signed.
    :param string unsigned_apk: Location of the apk product from the AaptBuilder task.
    :param Keystore object: Keystore instance with which to sign the android target.
    """
    # After JDK 1.7.0_51, jars without timestamps print a warning. This causes jars to stop working
    # past their validity date. But Android purposefully passes 30 years validity. More research
    # is needed before passing a -tsa flag indiscriminately.
    # http://bugs.java.com/view_bug.do?bug_id=8023338

    args = []
    args.extend([self.distribution.binary('jarsigner')])

    # These first two params are required flags for JDK 7+
    args.extend(['-sigalg', 'SHA1withRSA'])
    args.extend(['-digestalg', 'SHA1'])

    args.extend(['-keystore', key.keystore_location])
    args.extend(['-storepass', key.keystore_password])
    args.extend(['-keypass', key.key_password])
    args.extend(['-signedjar', (os.path.join(self.sign_apk_out(target, key.keystore_name),
                                             target.app_name + '.' + key.build_type +
                                             '.signed.apk'))])
    args.append(unsigned_apk)
    args.append(key.keystore_alias)
    return args

  def execute(self):
    with self.context.new_workunit(name='sign_apk', labels=[WorkUnit.MULTITOOL]):
      targets = self.context.targets(self.is_signtarget)
      #with self.invalidated(targets) as invalidation_check:
       # invalid_targets = []
        #for vt in invalidation_check.invalid_vts:
         # invalid_targets.extend(vt.targets)
      for target in targets: #invalid_targets:

          def get_apk(target):
            """Get a handle for the unsigned.apk product created by AaptBuilder."""
            unsigned_apks = self.context.products.get('apk')
            for tgts, products in unsigned_apks.get(target).items():
              unsigned_path = os.path.join(tgts)
              for prod in products:
                return os.path.join(unsigned_path, prod)

          unsigned_apk = get_apk(target)
          keystores = KeystoreResolver.resolve(self.config_file)
          for key in keystores:
            safe_mkdir(self.sign_apk_out(target, key.keystore_name))
            process = subprocess.Popen(self.render_args(target, unsigned_apk, key))
            result = process.wait()
            if result != 0:
              raise TaskError('Jarsigner tool exited non-zero ({code})'.format(code=result))

      # TODO(BEFORE REVIEW) DEFINE products
      # TODO(BEFORE REVIEW) Update read me in keystore_config.ini
      # TODO(BEFORE REVIEW) REmember invalidation framework

      #TODO(BEFORE REVIEW) Set up a test for no config file declared (the failure in the config_file property.)
        # Here is where we can update products to spin out to new tasks (see zipalign)
        # EXAMPLE
        # self.context.products.get('apk').add(target, self.workdir).append(target.app_name + "-unsigned.apk")


    #TODO(BEFORE REVIEW) Test case to ensure we can overwrite the pants.ini android_keystore_config entry

  # def execute(self):
  #
  #   with self.context.new_workunit(name='jarsigner', labels=[WorkUnit.MULTITOOL]):
  #     targets = self.context.targets(self.is_signtarget)
  #     with self.invalidated(targets) as invalidation_check:
  #       invalid_targets = []
  #       for vt in invalidation_check.invalid_vts:
  #         invalid_targets.extend(vt.targets)
  #       for target in invalid_targets:
  #         safe_mkdir(self.jarsigner_out(target))
  #         if self._build_type:
  #           build_type = self._build_type
  #         else:
  #           build_type = target.build_type
  #         keys = []
  #
  #         def get_apk(target):
  #           """Return the unsigned.apk product from AaptBuilder."""
  #           unsigned_apks = self.context.products.get('apk')
  #           for tgts, prods in unsigned_apks.get(target).items():
  #             unsigned_path = os.path.join(tgts)
  #             for prod in prods:
  #               return os.path.join(unsigned_path, prod)
  #
  #         def get_key(key):
  #           """Return Keystore objects that match the target's build_type."""
  #           if isinstance(key, Keystore):
  #             if key.build_type == build_type:
  #               keys.append(key)
  #
  #         unsigned_apk = get_apk(target)
  #         target.walk(get_key)
  #
  #         # Ensure there is only one key that matches the requested config.
  #         # Perhaps we will soon allow depending on multiple keys per type and match by name.
  #         if keys:
  #           if len(keys) > 1:
  #             raise TaskError(self, "This target: {0} depends on more than one key of the same "
  #                                   "build type [{1}]. Please pick just one key of each build type "
  #                                   "['debug', 'release']".format(target, target.build_type))
  #           # TODO(mateor?)create Nailgun pipeline for other java tools, handling stderr/out, etc.
  #           for key in keys:
  #             process = subprocess.Popen(self.render_args(target, unsigned_apk, key))
  #             result = process.wait()
  #             if result != 0:
  #               raise TaskError('Jarsigner tool exited non-zero ({code})'.format(code=result))
  #         else:
  #           raise TaskError(self, "No key matched the {0} target's build type "
  #                                 "[release, debug]".format(target))

  def sign_apk_out(self, target, key_name):
    #TODO (BEFORE REVIEW) fix this outdir pipeline so that it is not recomputed twice.
    # IF I cache this somewhere, then I can avoid passing target to render_args.
    # It willl already be implicit in the 'for target in targets' loop.
    return os.path.join(self._distdir, target.app_name, key_name)
