# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from collections import defaultdict
import os
import sys

from twitter.common.collections import OrderedSet
from twitter.common.lang import Compatibility


# Used to specify task-specific cmd-line flags. E.g.,
# ./pants compile;py -f <target>
TASK_SEPARATOR = ';'


class CommandLineArgumentError(Exception):
  pass


class Flags(object):
  """A set of command-line flags belonging to some context."""
  def __init__(self):
    self.flag_strings = OrderedSet()  # A set of flag strings.

  def add(self, flag_string):
    self.flag_strings.add(flag_string)


class GoalFlags(object):
  """Flags specified in the context of a goal.

  E.g., ./pants compile -f --no-read-from-artifact-cache <target>

  Some of these are specified in the context of a task within the goal,

  E.g., ./pants compile.java -f ./compile.scala -c <target>
  """
  def __init__(self):
    self.goalwide_flags = Flags()
    self.per_task_flags = defaultdict(Flags)  # task name -> Flags instance.


class CommandLineParserResult(object):
  """The result of a single parse."""
  def __init__(self):
    self.per_goal_flags = defaultdict(GoalFlags)  # goal name -> GoalFlags instance.
    self.global_flags = Flags()  # Flags not associated with a specific goal.
    self.targets = []

  def get_goals(self):
    return list(self.per_goal_flags.keys())

  def add_goal(self, goal):
    goal, _, _ = goal.partition(TASK_SEPARATOR)
    _ = self.per_goal_flags[goal]  # Inserts an empty value against the key.

  def add_flag(self, goal_context, flag):
    if goal_context:
      goal, sep, task = goal_context.partition(TASK_SEPARATOR)
      if sep:
        flags = self.per_goal_flags[goal].per_task_flags[task]
      else:
        flags = self.per_goal_flags[goal].goalwide_flags
    else:
      flags = self.global_flags
    flags.add(flag)


class CommandLineParser(object):
  """Parses a pants command-line."""

  def parse(self, args_to_parse=None):
    """Parse the args_to_parse, which may be:

    - None, in which case we use sys.argv.
    - An iterable of strings.
    - A single string, which we split on whitespace.

    In all cases the first arg is assumed to be the name of the binary, and is ignored.
    """
    # Accumulate the result here.
    result = CommandLineParserResult()

    # Figure out what we're parsing.
    if args_to_parse is None:
      args = sys.argv
    elif isinstance(args_to_parse, Compatibility.string):
      args = args_to_parse.split()
    else:
      args = args_to_parse

    args_iter = iter(args)

    try:
      # Skip the first arg, which we assume to be the name of the binary.
      args_iter.next()

      arg = args_iter.next()
      # Elide the superfluous word 'goal', which people may still specify for historical reasons.
      if arg == 'goal':
        arg = args_iter.next()

      current_goal_context = None
      accept_targets_only = False

      while True:
        if arg == '--':  # It's --.
          if result.targets:
            raise CommandLineArgumentError('Cannot intermix targets with goals when using -- . '
                                           'Targets must appear on the right.')
          else:
            accept_targets_only = True
        elif os.sep in arg or ':' in arg:  # It's a target spec.
          result.targets.append(arg)
          current_goal_context = None
        elif accept_targets_only:  # Are we allowed to accept anything else at this point?
          raise CommandLineArgumentError('%s is not a valid target spec.' % arg)
        elif arg.startswith('-'):  # It's a flag.
          result.add_flag(current_goal_context, arg)
        else: # It must be a goal name.
          result.add_goal(arg)
          current_goal_context = arg
        arg = args_iter.next()

    except StopIteration:
      pass

    return result

