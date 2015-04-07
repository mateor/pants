# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.tasks.aapt_gen import AaptGen
from pants_test.android.test_android_base import TestAndroidBase, distribution


class TestAaptGen(TestAndroidBase):
  """Test the methods in pants.backend.android.tasks.aapt_gen."""

  @classmethod
  def task_type(cls):
    return AaptGen

  def test_android_library_target(self):
    pass

  def test_aapt_gen_smoke(self):
    task = self.create_task(self.context())
    task.execute()

  def test_calculate_genfile(self):
    self.assertEqual(AaptGen._calculate_genfile('com.pants.examples.hello'),
                     os.path.join('com', 'pants', 'examples', 'hello', 'R.java'))

  def test_aapt_tool(self):
    with distribution() as dist:
      with self.android_binary() as android_binary:
        self.set_options(sdk_path=dist)
        task = self.create_task(self.context())
        target = android_binary
        self.assertEqual(task.aapt_tool(target.build_tools_version),
                         os.path.join(dist, 'build-tools', target.build_tools_version, 'aapt'))

  def test_android_tool(self):
    with distribution() as dist:
      with self.android_binary() as android_binary:
        self.set_options(sdk_path=dist)
        task = self.create_task(self.context())
        target = android_binary
        # Android jar is copied under the buildroot to comply with classpath rules.
        jar_folder = os.path.join(task.workdir, 'platforms',
                                  'android-{}'.format(target.manifest.target_sdk), 'android.jar')
        self.assertEqual(task.android_jar_tool(target.manifest.target_sdk), jar_folder)


  def test_render_args(self):
    with distribution() as dist:
      with self.android_resources() as android_resources:
        self.set_options(sdk_path=dist)
        task = self.create_task(self.context())
        target = android_resources
        expected_args = [task.aapt_tool(target.build_tools_version),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool(target.manifest.target_sdk),
                         '--ignore-assets', task.ignored_assets]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_render_args_force_ignored_assets(self):
    with distribution() as dist:
      with self.android_resources() as android_resources:
        ignored = '!picasa.ini:!*~:BUILD*'
        self.set_options(sdk_path=dist)
        task = self.create_task(self.context())
        target = android_resources
        expected_args = [task.aapt_tool(target.build_tools_version),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool(target.manifest.target_sdk),
                         '--ignore-assets', ignored]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_render_args_force_sdk(self):
    with distribution() as dist:
      with self.android_resources() as android_resources:
        sdk = '19'
        self.set_options(sdk_path=dist, target_sdk=sdk)
        task = self.create_task(self.context())
        target = android_resources
        expected_args = [task.aapt_tool(target.build_tools_version),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool('19'),
                         '--ignore-assets', task.ignored_assets]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_render_args_force_build_tools(self):
    with distribution() as dist:
      with self.android_resources() as android_resources:
        build_tools = '20.0.0'
        self.set_options(sdk_path=dist, build_tools_version=build_tools)
        task = self.create_task(self.context())
        target = android_resources
        expected_args = [task.aapt_tool(build_tools),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool(target.manifest.target_sdk),
                         '--ignore-assets', task.ignored_assets]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_createtarget(self):
    with distribution() as dist:
      with self.android_binary() as android_binary:
        self.set_options(sdk_path=dist)
        task = self.create_task(self.context())
        targets = [android_binary]
        task.create_sdk_jar_deps(targets)
        created_target = task.createtarget(android_binary, '19')
        self.assertEqual(created_target.derived_from, android_binary)
        self.assertEqual(created_target.is_synthetic, True)
