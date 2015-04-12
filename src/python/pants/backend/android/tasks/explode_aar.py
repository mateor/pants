# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.backend.android.tasks.android_task import AndroidTask


class ExplodeAar(AndroidTask):

  @classmethod
  def prepare(cls, options, round_manager):
    super(ExplodeAar, cls).prepare(options, round_manager)
    round_manager.require_data('ivy_imports')

    #round_manager.require_data('jar_dependencies')

  @classmethod
  def product_types(cls):
    return ['exploded_aars']

  def execute(self):
    print("LADIES AND GENTLEMEN WE ARE FLOATING IN THE EXPLODE_AAR TASK....")
    targets = self.context.targets()
    products = self.context.products.get('ivy_imports')
    jarmap = products[unpacked_jars]
    print("THE CLASSPATH OBJECTS ARE: ", classpath_products)
