# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.android.tasks.aapt_gen import AaptGen
from pants_test.android.test_android_base import TestAndroidBase


class TestAaptGen(TestAndroidBase):
  """Test the methods in pants.backend.android.tasks.aapt_gen."""

  @classmethod
  def task_type(cls):
    return AaptGen

  def test_aapt_gen_smoke(self):
    task = self.prepare_task(build_graph=self.build_graph,
                             build_file_parser=self.build_file_parser)
    task.execute()

  def test_calculate_genfile(self):
    self.assertEqual(AaptGen._calculate_genfile('com.pants.examples.hello'),
                     os.path.join('com', 'pants', 'examples', 'hello', 'R.java'))

  def test_aapt_tool(self):
    with self.distribution() as dist:
      with self.android_binary() as android_binary:
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_binary
        self.assertEqual(task.aapt_tool(target.build_tools_version),
                         os.path.join(dist, 'build-tools', target.build_tools_version, 'aapt'))

  def test_android_tool(self):
    with self.distribution() as dist:
      with self.android_binary() as android_binary:
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_binary
        # Android jar is copied under the buildroot to comply with classpath rules.
        jar_folder = os.path.join(task.workdir, 'platforms',
                                  'android-{}'.format(target.manifest.target_sdk), 'android.jar')
        self.assertEqual(task.android_jar_tool(target.manifest.target_sdk), jar_folder)


  def test_render_args(self):
    with self.distribution() as dist:
      with self.android_test_resources() as android_resources:
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_resources
        expected_args = [task.aapt_tool(target.build_tools_version),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool(target.manifest.target_sdk),
                         '--ignore-assets', task.ignored_assets]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_render_args_force_ignored_assets(self):
    with self.distribution() as dist:
      with self.android_test_resources() as android_resources:
        ignored = '!picasa.ini:!*~:BUILD*'
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist),
                                       '--test-ignored-assets={0}'.format(ignored)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_resources
        expected_args = [task.aapt_tool(target.build_tools_version),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool(target.manifest.target_sdk),
                         '--ignore-assets', ignored]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_render_args_force_sdk(self):
    with self.distribution() as dist:
      with self.android_test_resources() as android_resources:
        sdk = '19'
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist),
                                       '--test-target-sdk={0}'.format(sdk)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_resources
        expected_args = [task.aapt_tool(target.build_tools_version),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool('19'),
                         '--ignore-assets', task.ignored_assets]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_render_args_force_build_tools(self):
    with self.distribution() as dist:
      with self.android_test_resources() as android_resources:
        build_tools = '20.0.0'
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist),
                                       '--test-build-tools-version={0}'.format(build_tools)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        target = android_resources
        expected_args = [task.aapt_tool(build_tools),
                         'package', '-m', '-J', task.workdir,
                         '-M', target.manifest.path,
                         '-S', target.resource_dir,
                         '-I', task.android_jar_tool(target.manifest.target_sdk),
                         '--ignore-assets', task.ignored_assets]
        self.assertEqual(expected_args, task._render_args(target, task.workdir))

  def test_createtarget(self):
    with self.distribution() as dist:
      with self.android_binary() as android_binary:
        task = self.prepare_task(args=['--test-sdk-path={0}'.format(dist)],
                                 build_graph=self.build_graph,
                                 build_file_parser=self.build_file_parser)
        targets = [android_binary]
        task.prepare_gen(targets)
        created_target = task.createtarget(android_binary, [])
        self.assertEqual(created_target.derived_from, android_binary)
        self.assertEqual(created_target.is_synthetic, True)
