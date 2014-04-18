# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_library(
  name='config',
  dependencies = [
    ':command-line-parser'
  ]
)

python_library(
  name = 'command-line-parser',
  sources = ['command_line_parser.py'],
  dependencies = [
    pants('3rdparty/python/twitter/commons:twitter.common.collections'),
    pants('3rdparty/python/twitter/commons:twitter.common.lang'),
  ]
)
