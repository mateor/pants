# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from pants.base.target import Target

class AndroidTarget(Target):
    """A base class for all Android targets"""

    def __init__(self,
                 address=None,
                 sources=None,
                 sources_rel_path=None,
                 excludes=None,
                 resources=None,
                 **kwargs):
        """
        :param address:
        :param sources:
        :param sources_rel_path:
        :param excludes:
        :param resources:
        :param kwargs:
        :return:
        """