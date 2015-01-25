# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import textwrap

from pants.util.contextutil import temporary_dir, temporary_file

from pants.backend.android.tasks.sign_apk import SignApkTask
from pants.backend.android.targets.android_binary import AndroidBinary
from pants.base.build_file_aliases import BuildFileAliases
from pants.base.exceptions import TaskError
from pants_test.tasks.test_base import TaskTest


class SignApkTest(TaskTest):
  """Test the package signing methods in pants.backend.android.tasks."""

  _DEFAULT_KEYSTORE = '%(homedir)s/.doesnt/matter/keystore_config.ini'

  class FakeKeystore(object):
    # Mock keystores so as to test the render_args method.
    def __init__(self):
      self.build_type = 'debug'
      self.keystore_name='key_name'
      self.keystore_location = '/path/to/key'
      self.keystore_alias = 'key_alias'
      self.keystore_password = 'keystore_password'
      self.key_password = 'key_password'

  class FakeDistribution(object):
    # Mock JDK distribution so as to test the render_args method.
    @classmethod
    def binary(self, tool):
      return 'path/to/{0}'.format(tool)

  @classmethod
  def task_type(cls):
    return SignApkTask

  @property
  def alias_groups(self):
    return BuildFileAliases.create(targets={'android_binary': AndroidBinary})

  def _get_config(self,
                  section=SignApkTask._CONFIG_SECTION,
                  option='keystore_config_location',
                  location=_DEFAULT_KEYSTORE):
    ini = textwrap.dedent( """
    [{0}]

    {1}: {2}
    """).format(section, option, location)
    return ini


  def android_binary(self):
    with temporary_file() as fp:
      fp.write(textwrap.dedent(
        """<?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android"
            package="com.pants.examples.hello" >
            <uses-sdk
                android:minSdkVersion="8"
                android:targetSdkVersion="19" />
        </manifest>
        """))
      path = fp.name
      fp.close()
      # With no android:name field, the app name defaults to the target name.
      target = self.make_target(spec=':binary',
                                target_type=AndroidBinary,
                                manifest=path)
      return target

  def test_sign_apk_smoke(self):
    task = self.prepare_task(config=self._get_config(),
                             build_graph=self.build_graph,
                             build_file_parser=self.build_file_parser)
    task.execute()

  def test_config_file(self):
    task = self.prepare_task(config=self._get_config(),
                             build_graph=self.build_graph,
                             build_file_parser=self.build_file_parser)
    task.config_file

  def test_no_config_file_defined(self):
    with self.assertRaises(TaskError):
      task = self.prepare_task(config=self._get_config(location=""),
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      task.config_file

  def test_config_file_from_pantsini(self):
    with temporary_dir() as temp:
      task = self.prepare_task(config=self._get_config(location=temp),
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      task.execute()
      task.config_file
      self.assertEquals(temp, task.config_file)

  def test_no_matching_section_in_pantsini(self):
    with self.assertRaises(TaskError):
      task = self.prepare_task(config=self._get_config(location=""),
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      task.config_file

  def test_passing_config_on_cli(self):
    with temporary_dir() as temp:
      task = self.prepare_task(config=self._get_config(section="bad-section-header"),
                               args=['--test-keystore-config-location={0}'.format(temp)],
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      task.config_file


  def test_passing_bad_config_on_cli(self):
    with self.assertRaises(TaskError):
      task = self.prepare_task(args=['--test-keystore-config-location={0}'.format("")],
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
      task.config_file

  def test_render_args(self):
    with temporary_dir() as temp:
      task = self.prepare_task(config=self._get_config(section="bad-section-header"),
                               args=['--test-keystore-config-location={0}'.format(temp)],
                               build_graph=self.build_graph,
                               build_file_parser=self.build_file_parser)
    target = self.android_binary()
    self.assertEquals(target.app_name, 'binary')
    fake_key = self.FakeKeystore()
    task._dist = self.FakeDistribution()
    expected_args = ['path/to/jarsigner',
                      '-sigalg', 'SHA1withRSA', '-digestalg', 'SHA1',
                      '-keystore', '/path/to/key',
                      '-storepass', 'keystore_password',
                      '-keypass', 'key_password',
                      '-signedjar']
    expected_args.extend(['{0}/binary.debug.signed.apk'.format(task.sign_apk_out(target, fake_key.keystore_name))])
    expected_args.extend(['unsigned_apk_product', 'key_alias'])
    self.assertEquals(expected_args, task.render_args(target, 'unsigned_apk_product', fake_key))

