# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import copy
import warnings
from argparse import ArgumentParser, _HelpAction
from collections import defaultdict

import six

from pants.base.deprecated import check_deprecated_semver
from pants.option.arg_splitter import GLOBAL_SCOPE
from pants.option.errors import ParseError, RegistrationError
from pants.option.help_formatter import HelpFormatter
from pants.option.help_info_extracter import HelpInfoExtracter
from pants.option.option_util import is_boolean_flag
from pants.option.ranked_value import RankedValue


# Standard ArgumentParser prints usage and exits on error. We subclass so we can raise instead.
# Note that subclassing ArgumentParser for this purpose is allowed by the argparse API.
class CustomArgumentParser(ArgumentParser):
  def __init__(self, scope, *args, **kwargs):
    super(CustomArgumentParser, self).__init__(*args, **kwargs)
    self._scope = scope

  def error(self, message):
    scope = 'global' if self._scope == GLOBAL_SCOPE else self._scope
    raise ParseError('{0} in {1} scope'.format(message, scope))

  def walk_actions(self):
    """Iterates over the argparse.Action objects for options registered on this parser."""
    for action_group in self._action_groups:
      for action in action_group._group_actions:
        if not isinstance(action, _HelpAction):
          yield action


class Parser(object):
  """An argument parser in a hierarchy.

  Each node in the hierarchy is a 'scope': the root is the global scope, and the parent of
  a node is the scope it's immediately contained in. E.g., the 'compile.java' scope is
  a child of the 'compile' scope, which is a child of the global scope.

  Options registered on a parser are also registered transitively on all the scopes it encloses.
  Registration must be in outside-in order: we forbid registering options on an outer scope if
  we've already registered an option on one of its inner scopes. This is to ensure that
  re-registering the same option name on an inner scope correctly replaces the identically-named
  option from the outer scope.

  :param env: a dict of environment variables.
  :param config: data from a config file (must support config.get[list](section, name, default=)).
  :param scope: the scope this parser acts for.
  :param parent_parser: the parser for the scope immediately enclosing this one, or
         None if this is the global scope.
  """

  class BooleanConversionError(ParseError):
    """Raised when a value other than 'True' or 'False' is encountered."""
    pass

  @staticmethod
  def str_to_bool(s):
    if isinstance(s, six.string_types):
      if s.lower() == 'true':
        return True
      elif s.lower() == 'false':
        return False
      else:
        raise Parser.BooleanConversionError('Got "{0}". Expected "True" or "False".'.format(s))
    if s is True:
      return True
    elif s is False:
      return False
    else:
      raise Parser.BooleanConversionError('Got {0}. Expected True or False.'.format(s))

  def __init__(self, env, config, scope_info, parent_parser):
    self._env = env
    self._config = config
    self._scope_info = scope_info
    self._scope = self._scope_info.scope

    # If True, no more registration is allowed on this parser.
    self._frozen = False

    # List of (args, kwargs) registration pairs, captured at registration time.
    # Note that the kwargs may include our custom, non-argparse arguments
    # (e.g., 'recursive' and 'advanced').
    self._registration_args = []

    # The argparser we use for actually parsing args.
    self._argparser = CustomArgumentParser(scope=self._scope, conflict_handler='resolve')

    # Map of external to internal dest names, and its inverse. See docstring for _set_dest below.
    self._dest_forwardings = {}
    self._inverse_dest_forwardings = defaultdict(set)

    # Map of dest -> (deprecated_version, deprecated_hint), for deprecated options.
    # The keys are external dest names (the ones seen by the user, not by argparse).
    self._deprecated_option_dests = {}

    # A Parser instance, or None for the global scope parser.
    self._parent_parser = parent_parser

    # List of Parser instances.
    self._child_parsers = []

    if self._parent_parser:
      self._parent_parser._register_child_parser(self)

  @property
  def scope(self):
    return self._scope

  def walk(self, callback):
    """Invoke callback on this parser and its descendants, in depth-first order."""
    callback(self)
    for child in self._child_parsers:
      child.walk(callback)

  def parse_args(self, args, namespace):
    """Parse the given args and set their values onto the namespace object's attributes."""
    namespace.add_forwardings(self._dest_forwardings)
    new_args = vars(self._argparser.parse_args(args))
    namespace.update(new_args)

    # Check for deprecated flags.
    all_deprecated_dests = set(self._deprecated_option_dests.keys())
    for internal_dest in new_args.keys():
      external_dests = self._inverse_dest_forwardings.get(internal_dest, set())
      deprecated_dests = all_deprecated_dests & external_dests
      if deprecated_dests:
        # Check all dests. Typically there is only one, unless the option was registered with
        # multiple aliases (which we almost never do).  And in any case we'll only warn for the
        # ones actually used on the cmd line.
        for dest in deprecated_dests:
          if namespace.get_rank(dest) == RankedValue.FLAG:
            warnings.warn('*** {}'.format(self._deprecated_message(dest)), DeprecationWarning,
                          stacklevel=9999) # Out of range stacklevel to suppress printing src line.
    return namespace

  def get_help_info(self):
    """Returns a dict of help information for the options registered on this object.

    Callers can format this dict into cmd-line help, HTML or whatever.
    """
    return HelpInfoExtracter(self._scope).get_option_scope_help_info(self._registration_args)

  def format_help(self, header, show_advanced=False, color=True):
    """Return a help message for the options registered on this object."""
    help_formatter = HelpFormatter(scope=self._scope, show_advanced=show_advanced, color=color)
    return '\n'.join(help_formatter.format_options(header, self._registration_args))

  def register(self, *args, **kwargs):
    """Register an option, using argparse params.

    Custom extensions to argparse params:
    :param advanced: if True, the option will be suppressed when displaying help.
    :param deprecated_version: Mark an option as deprecated.  The value is a semver that indicates
       the release at which the option should be removed from the code.
    :param deprecated_hint: A message to display to the user when displaying help for or invoking
       a deprecated option.
    """
    if self._frozen:
      raise RegistrationError('Cannot register option {0} in scope {1} after registering options '
                              'in any of its inner scopes.'.format(args[0], self._scope))

    # Prevent further registration in enclosing scopes.
    ancestor = self._parent_parser
    while ancestor:
      ancestor._freeze()
      ancestor = ancestor._parent_parser

    self._validate(args, kwargs)
    dest = self._set_dest(args, kwargs)
    if 'recursive' in kwargs:
      kwargs['recursive_root'] = True  # So we can distinguish the original registrar.
    self._register(dest, args, kwargs)  # Note: May modify kwargs (to remove recursive_root).

  def _deprecated_message(self, dest):
    """Returns the message to be displayed when a deprecated option is specified on the cmd line.

    Assumes that the option is indeed deprecated.

    :param dest: The dest of the option being invoked.
    """
    deprecated_version, deprecated_hint = self._deprecated_option_dests[dest]
    scope = self._scope or 'DEFAULT'
    message = 'Option {dest} in scope {scope} is deprecated and will be removed in version ' \
              '{removal_version}'.format(dest=dest, scope=scope,
                                         removal_version=deprecated_version)
    hint = deprecated_hint or ''
    return '{}. {}'.format(message, hint)

  def _clean_argparse_kwargs(self, dest, args, kwargs):
    ranked_default = self._compute_default(dest, kwargs=kwargs)
    kwargs_with_default = dict(kwargs, default=ranked_default)
    self._registration_args.append((args, kwargs_with_default))

    # For argparse registration, remove our custom kwargs.
    argparse_kwargs = dict(kwargs_with_default)
    argparse_kwargs.pop('advanced', False)
    recursive = argparse_kwargs.pop('recursive', False)
    argparse_kwargs.pop('recursive_root', False)
    argparse_kwargs.pop('registering_class', None)
    deprecated_version = argparse_kwargs.pop('deprecated_version', None)
    deprecated_hint = argparse_kwargs.pop('deprecated_hint', '')

    if deprecated_version is not None:
      check_deprecated_semver(deprecated_version)
      self._deprecated_option_dests[dest] = (deprecated_version, deprecated_hint)

    return argparse_kwargs, recursive

  def _register(self, dest, args, kwargs):
    """Register the option for parsing (recursively if needed)."""
    argparse_kwargs, recursive = self._clean_argparse_kwargs(dest, args, kwargs)
    if is_boolean_flag(argparse_kwargs):
      inverse_args = self._create_inverse_args(args)
      if inverse_args:
        inverse_argparse_kwargs = self._create_inverse_kwargs(argparse_kwargs)
        group = self._argparser.add_mutually_exclusive_group()
        group.add_argument(*args, **argparse_kwargs)
        group.add_argument(*inverse_args, **inverse_argparse_kwargs)
      else:
        self._argparser.add_argument(*args, **argparse_kwargs)
    else:
      self._argparser.add_argument(*args, **argparse_kwargs)

    if recursive:
      # Propagate registration down to inner scopes.
      for child_parser in self._child_parsers:
        kwargs.pop('recursive_root', False)
        child_parser._register(dest, args, kwargs)

  def _validate(self, args, kwargs):
    """Ensure that the caller isn't trying to use unsupported argparse features."""
    for arg in args:
      if not arg.startswith('-'):
        raise RegistrationError('Option {0} in scope {1} must begin '
                                'with a dash.'.format(arg, self._scope))
      if not arg.startswith('--') and len(arg) > 2:
        raise RegistrationError('Multicharacter option {0} in scope {1} must begin '
                                'with a double-dash'.format(arg, self._scope))
    if 'nargs' in kwargs and kwargs['nargs'] != '?':
      raise RegistrationError('nargs={0} unsupported in registration of option {1} in '
                              'scope {2}.'.format(kwargs['nargs'], args, self._scope))
    if 'required' in kwargs:
      raise RegistrationError('required unsupported in registration of option {0} in '
                              'scope {1}.'.format(args, self._scope))

  def _set_dest(self, args, kwargs):
    """Maps the externally-used dest to a scoped one only seen internally.

    If an option is re-registered in an inner scope, it'll shadow the external dest but will
    use a different internal one. This is important in the case that an option is registered
    with two names (say -x, --xlong) and we only re-register one of them, say --xlong, in an
    inner scope. In this case we no longer want them to write to the same dest, so we can
    use both (now with different meanings) in the inner scope.

    Note: Modfies kwargs.
    """
    dest = self._select_dest(args, kwargs)
    scoped_dest = '_{0}_{1}__'.format(self._scope or 'DEFAULT', dest)

    # Make argparse write to the internal dest.
    kwargs['dest'] = scoped_dest

    def add_forwarding(x, y):
      self._dest_forwardings[x] = y
      self._inverse_dest_forwardings[y].add(x)

    # Make reads from the external dest forward to the internal one.
    add_forwarding(dest, scoped_dest)

    # Also forward all option aliases, so we can reference -x (as options.x) in the example above.
    for arg in args:
      add_forwarding(arg.lstrip('-').replace('-', '_'), scoped_dest)
    return dest

  def _select_dest(self, args, kwargs):
    """Select the dest name for the option.

    Replicated from the dest inference logic in argparse:
    '--foo-bar' -> 'foo_bar' and '-x' -> 'x'.
    """
    dest = kwargs.get('dest')
    if dest:
      return dest
    arg = next((a for a in args if a.startswith('--')), args[0])
    return arg.lstrip('-').replace('-', '_')

  def _compute_default(self, dest, kwargs):
    """Compute the default value to use for an option's registration.

    The source of the default value is chosen according to the ranking in RankedValue.
    """
    config_section = 'DEFAULT' if self._scope == GLOBAL_SCOPE else self._scope
    udest = dest.upper()
    if self._scope == GLOBAL_SCOPE:
      # For convenience, we allow three forms of env var for global scope options.
      # The fully-specified env var is PANTS_DEFAULT_FOO, which is uniform with PANTS_<SCOPE>_FOO
      # for all the other scopes.  However we also allow simply PANTS_FOO. And if the option name
      # itself starts with 'pants-' then we also allow simply FOO. E.g., PANTS_WORKDIR instead of
      # PANTS_PANTS_WORKDIR or PANTS_DEFAULT_PANTS_WORKDIR. We take the first specified value we
      # find, in this order: PANTS_DEFAULT_FOO, PANTS_FOO, FOO.
      env_vars = ['PANTS_DEFAULT_{0}'.format(udest), 'PANTS_{0}'.format(udest)]
      if udest.startswith('PANTS_'):
        env_vars.append(udest)
    else:
      env_vars = ['PANTS_{0}_{1}'.format(config_section.upper().replace('.', '_'), udest)]
    value_type = self.str_to_bool if is_boolean_flag(kwargs) else kwargs.get('type', str)
    env_val_str = None
    if self._env:
      for env_var in env_vars:
        if env_var in self._env:
          env_val_str = self._env.get(env_var)
          break
    env_val = None if env_val_str is None else value_type(env_val_str)
    if kwargs.get('action') == 'append':
      config_val_strs = self._config.getlist(config_section, dest) if self._config else None
      config_val = (None if config_val_strs is None else
                    [value_type(config_val_str) for config_val_str in config_val_strs])
      default = []
    else:
      config_val_str = (self._config.get(config_section, dest, default=None)
                        if self._config else None)
      config_val = None if config_val_str is None else value_type(config_val_str)
      default = None
    hardcoded_val = kwargs.get('default')
    return RankedValue.choose(None, env_val, config_val, hardcoded_val, default)

  def _create_inverse_args(self, args):
    inverse_args = []
    for arg in args:
      if arg.startswith('--'):
        if arg.startswith('--no-'):
          raise RegistrationError(
            'Invalid option name "{}". Boolean options names cannot start with --no-'.format(arg))
        inverse_args.append('--no-{}'.format(arg[2:]))
    return inverse_args

  def _create_inverse_kwargs(self, kwargs):
    """Create the kwargs for registering the inverse of a boolean flag."""
    inverse_kwargs = copy.copy(kwargs)
    inverse_action = 'store_true' if kwargs.get('action') == 'store_false' else 'store_false'
    inverse_kwargs['action'] = inverse_action
    inverse_kwargs.pop('default', None)
    return inverse_kwargs

  def _register_child_parser(self, child):
    self._child_parsers.append(child)

  def _freeze(self):
    self._frozen = True

  def __str__(self):
    return 'Parser({})'.format(self._scope)
