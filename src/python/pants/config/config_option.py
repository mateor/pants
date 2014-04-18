# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)


class ConfigOption(object):
  """Registry of pants.ini options.

  Options are created in code, typically scoped as close to their use as possible. ::

     my_opt = ConfigOption.create(
       section='mycache',
       option='workdir',
       help='Directory, relative to pants_workdir, of the mycache workdir.',
       default='mycache')

  Read an option from ``pants.ini`` with ::

     mycache_dir = os.path.join(config.get_option(config.DEFAULT_PANTS_WORKDIR),
                                config.get_option(_REPORTING_REPORTS_DIR))

  Please note `configparser <http://docs.python.org/2/library/configparser.html>`_
  is used to retrieve options, so variable interpolation and the default section
  are used as defined in the configparser docs.
  """

  class Option(object):
    """A ``pants.ini`` option."""
    def __init__(self, section, option, help_str, valtype, default):
      """Do not instantiate directly - use ConfigOption.create."""
      self.section = section
      self.option = option
      self.help = help_str
      self.valtype = valtype
      self.default = default

    def __hash__(self):
      return hash(self.section + self.option)

    def __eq__(self, other):
      if other is None:
        return False
      return True if self.section == other.section and self.option == other.option else False

    def __repr__(self):
      return '%s(%s.%s)' % (self.__class__.__name__, self.section, self.option)

  _CONFIG_OPTIONS = set()

  @classmethod
  def all(cls):
    return cls._CONFIG_OPTIONS

  @classmethod
  def create(cls, section, option, help, valtype=str, default=None):
    """Create a new ``pants.ini`` option.

    :param section: Name of section to retrieve option from.
    :param option: Name of option to retrieve from section.
    :param help: Description for display in the configuration reference.
    :param valtype: Type to cast the retrieved option to.
    :param default: Default value if undefined in the config.
    :returns: An ``Option`` suitable for use with ``Config.get_option``.
    :raises: ``ValueError`` if the option already exists.
    """
    new_opt = cls.Option(section=section,
                         option=option,
                         help=help,
                         valtype=valtype,
                         default=default)
    for existing_opt in cls._CONFIG_OPTIONS:
      if new_opt.section == existing_opt.section and new_opt.option == existing_opt.option:
        raise ValueError('Option %s.%s already exists.' % (new_opt.section, new_opt.option))
    cls._CONFIG_OPTIONS.add(new_opt)
    return new_opt
