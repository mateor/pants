# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from textwrap import dedent


def valid_classfile():
  class_text = dedent('''
  #
  # sample small-but-valid classfile
  #

  cafe babe  # magic
  0000       # minor_version
  002e       # major_version
  000c       # constant_pool_count

  #
  # constant_pool
  #
  07 0003                       # 0001: class[Small]
  07 0004                       # 0002: class[java/lang/Object]
  01 0005 "Small"               # 0003: utf8["Small"]
  01 0010 "java/lang/Object"    # 0004: utf8["java/lang/Object"]
  01 0005 "blort"               # 0005: utf8["blort"]
  01 0003 "()V"                 # 0006: utf8["()V"]
  01 0004 "Code"                # 0007: utf8["Code"]
  01 000f "java/lang/Error"     # 0008: utf8["java/lang/Error"]
  01 0013 "java/lang/Exception" # 0009: utf8["java/lang/Exception"]
  07 0008                       # 000a: class[java/lang/Error]
  07 0009                       # 000b: class[java/lang/Exception]

  0001  # access_flags
  0001  # this_class
  0002  # super_class
  0000  # interfaces_count
  0000  # fields_count
  0001  # methods_count

  # methods[0]
  0001  # access_flags
  0005  # name
  0006  # descriptor
  0001  # attributes_count
  # attributes[0]
  0007      # name
  00000027  # length
  0001      # max_stack
  0001      # max_locals
  00000003  # code_length
  b1        # 0000: return
  b1        # 0001: return
  b1        # 0002: return
  0003      # exception_table_length
  0000 0002 0002 000a  # 0000..0002 -> 0002 java/lang/Error
  0000 0001 0001 000b  # 0000..0001 -> 0001 java/lang/Exception
  0001 0002 0002 0000  # 0001..0002 -> 0002 <any>
  0000      # attributes_count

  0000  # attributes_count
  ''')
  return class_text
