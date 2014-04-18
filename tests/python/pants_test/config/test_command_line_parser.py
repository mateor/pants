# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import unittest

from pants.config.command_line_parser import CommandLineArgumentError, CommandLineParser


class CommandLineParserTest(unittest.TestCase):
  def _diff(self, result, expected_result):
    # result is a CommandLineParserResult, expected_result is a dict.
    self.assertEquals(result.goals, expected_result[''])
    self.assertEquals(result.global_flags, expected_result['global_flags'])


  def _do_test(self, args, expected_goals, expected_targets,
               expected_global_flags=None, expected_goal_flags=None, expected_task_flags=None):
    result = CommandLineParser().parse(args)

    # Convert the result structures to dicts-and-lists, for easy comparison.
    global_flags = list(result.global_flags.flag_strings)
    goal_flags = {}
    task_flags = {}

    for goal, gflags in result.per_goal_flags.items():
      if gflags.goalwide_flags.flag_strings:
        goal_flags[goal] = list(gflags.goalwide_flags.flag_strings)
      for task, tflags in gflags.per_task_flags.items():
        if tflags.flag_strings:
          if goal not in task_flags:
            task_flags[goal] = {}
          task_flags[goal][task] = list(tflags.flag_strings)

    self.assertEquals(expected_goals, result.get_goals())
    self.assertEquals(expected_targets, result.targets)
    self.assertEquals(expected_global_flags or [], global_flags)
    self.assertEquals(expected_goal_flags or {}, goal_flags)
    self.assertEquals(expected_task_flags or {}, task_flags)

  def test_parsing(self):
    self._do_test('', [], [])
    self._do_test('./pants', [], [])
    self._do_test('./pants goal', [], [])

    self._do_test('./pants compile foo/bar/baz', ['compile'], ['foo/bar/baz'])

    self._do_test('./pants goal compile foo/bar/baz', ['compile'], ['foo/bar/baz'])

    self._do_test('./pants goal compile -v foo/bar/baz --long-flag test -s',
                  ['compile', 'test'],
                  ['foo/bar/baz'],
                  ['--long-flag'],
                  { 'compile': ['-v'], 'test': ['-s'] })

    self._do_test('./pants compile;java -a compile;scala -b foo/bar/baz --long-flag test -s',
                  ['compile', 'test'],
                  ['foo/bar/baz'],
                  ['--long-flag'],
                  { 'test': ['-s'] },
                  { 'compile': {'java': ['-a'], 'scala': ['-b'] } })

    self._do_test('./pants compile;java -a --c compile;scala -b test -s foo/bar/baz foo/bar/baz2',
                  ['compile', 'test'],
                  ['foo/bar/baz', 'foo/bar/baz2'],
                  [],
                  { 'test': ['-s'] },
                  { 'compile': {'java': ['-a', '--c'], 'scala': ['-b'] } })

    self._do_test('./pants --foo compile;java -a :bar -z compile -b test;scala -s '
                  'test -x -y bundle',
                  ['compile', 'test', 'bundle'],
                  [':bar'],
                  ['--foo', '-z'],
                  { 'compile': ['-b'], 'test': ['-x', '-y'] },
                  { 'compile': {'java': ['-a'] }, 'test': { 'scala': ['-s'] } })

    self._do_test('./pants --foo compile;java -a -z compile -b test;scala -s '
                  'test -x -y bundle -- :bar foo/bar:baz',
                  ['compile', 'test', 'bundle'],
                  [':bar', 'foo/bar:baz'],
                  ['--foo'],
                  { 'compile': ['-b'], 'test': ['-x', '-y'] },
                  { 'compile': {'java': ['-a', '-z'] }, 'test': { 'scala': ['-s'] } })


  def test_parse_errors(self):
    self.assertRaises(CommandLineArgumentError,
      lambda: CommandLineParser().parse('./pants goal compile :foo -- :bar'))