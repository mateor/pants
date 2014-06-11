# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from pants.base.build_manual import manual
from pants.backend.android.targets.android_target import AndroidTarget

@manual.builddict(tags=["android"])
class AndroidResources(AndroidTarget):
  """Generates an R class from android resource files. This allows resources to be referenced from java code"""

  def __init__(self, **kwargs):
    """
    :param name: Name of target
    :param resources: folder that holds the resource files #TODO: For now. Still debating resource keyword placement
    :param dependencies: List of :class:`pants.base.target.Target` instances
      this target depends on.
    :type dependencies: list of targets
    :param dict exclusives: An optional dict of exclusives tags. See CheckExclusives for details.
    """

    super(AndroidResources, self).__init__(**kwargs)
    self.add_labels('codegen')