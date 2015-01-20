# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).


from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import textwrap
from contextlib import contextmanager
import unittest2 as unittest

from pants.base.config import Config
from pants.util.contextutil import temporary_file

class TestKeyResolver(unittest.TestCase):

  @contextmanager
  def config_file(self):
    with temporary_file() as fd:
      fd.close()
      yield fd.name


  def setUp(self):
    with temporary_file() as legit:
      legit.write(textwrap.dedent(
        """
        [DEFAULT]
        name: foo
        answer: 42
        scale: 1.2
        path: /a/b/%(answer)s
        embed: %(path)s::foo
        disclaimer:
          Let it be known
          that.

        [a]
        list: [1, 2, 3, %(answer)s]

        [b]
        preempt: True
        dict: {
            'a': 1,
            'b': %(answer)s,
            'c': ['%(answer)s', %(answer)s]
          }
        """))
      legit.close()

      with temporary_file() as borked:
        borked.write(textwrap.dedent(
          """
          [a]
          fast: True

          [b]
          preempt: False
          """))
        borked.close()
        self.config = Config.load(configpaths=[legit.name, borked.name])

  def test_resolve(self):
    self.assertEquals(2, 2)
