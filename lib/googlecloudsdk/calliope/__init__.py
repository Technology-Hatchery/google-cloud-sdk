# Copyright 2013 Google Inc. All Rights Reserved.

"""The calliope CLI/API is a framework for building library interfaces."""

import abc
import argparse
import errno
import imp
import json
import os
import pprint
import re
import sys
import textwrap
import uuid
import argcomplete

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import shell
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties


class LayoutException(Exception):
  """LayoutException is for problems with module directory structure."""
  pass


class ArgumentException(Exception):
  """ArgumentException is for problems with the provided arguments."""
  pass


class MissingArgumentException(ArgumentException):
  """An exception for when required arguments are not provided."""

  def __init__(self, command_path, missing_arguments):
    """Creates a new MissingArgumentException.

    Args:
      command_path: A list representing the command or group that had the
          required arguments
      missing_arguments: A list of the arguments that were not provided
    """
    message = ('The following required arguments were not provided for command '
               '[{0}]: [{1}]'.format('.'.join(command_path),
                                     ', '.join(missing_arguments)))
    super(MissingArgumentException, self).__init__(message)


class UnexpectedArgumentException(ArgumentException):
  """An exception for when required arguments are not provided."""

  def __init__(self, command_path, unexpected_arguments):
    """Creates a new UnexpectedArgumentException.

    Args:
      command_path: A list representing the command or group that was given the
          unexpected arguments
      unexpected_arguments: A list of the arguments that were not valid
    """
    message = ('The following arguments were unexpected for command '
               '[{0}]: [{1}]'.format('.'.join(command_path),
                                     ', '.join(unexpected_arguments)))
    super(UnexpectedArgumentException, self).__init__(message)


class CommandLoadFailure(Exception):
  """An exception for when a command or group module cannot be imported."""

  def __init__(self, command, root_exception):
    self.command = command
    self.root_exception = root_exception
    super(CommandLoadFailure, self).__init__(
        'Problem loading {command}: {issue}.'.format(
            command=command, issue=str(root_exception)))


class _Args(object):
  """A helper class to convert a dictionary into an object with properties."""

  def __init__(self, args):
    self.__dict__.update(args)

  def __str__(self):
    return '_Args(%s)' % pprint.pformat(self.__dict__)

  def __iter__(self):
    for key, value in sorted(self.__dict__.iteritems()):
      yield key, value


class _ArgumentInterceptor(object):
  """_ArgumentInterceptor intercepts calls to argparse parsers.

  The argparse module provides no public way to access a complete list of
  all arguments, and we need to know these so we can do validation of arguments
  when this library is used in the python interpreter mode. Argparse itself does
  the validation when it is run from the command line.

  Attributes:
    parser: argparse.Parser, The parser whose methods are being intercepted.
    allow_positional: bool, Whether or not to allow positional arguments.
    defaults: {str:obj}, A dict of {dest: default} for all the arguments added.
    required: [str], A list of the dests for all required arguments.
    dests: [str], A list of the dests for all arguments.
    positional_args: [argparse.Action], A list of the positional arguments.
    flag_args: [argparse.Action], A list of the flag arguments.

  Raises:
    ArgumentException: if a positional argument is made when allow_positional
        is false.
  """

  class ParserData(object):

    def __init__(self):
      self.defaults = {}
      self.required = []
      self.dests = []
      self.mutex_groups = {}
      self.positional_args = []
      self.flag_args = []
      self.ancestor_flag_args = []

  def __init__(self, parser, allow_positional, data=None, mutex_group_id=None):
    self.parser = parser
    self.allow_positional = allow_positional
    self.data = data or _ArgumentInterceptor.ParserData()
    self.mutex_group_id = mutex_group_id

  @property
  def defaults(self):
    return self.data.defaults

  @property
  def required(self):
    return self.data.required

  @property
  def dests(self):
    return self.data.dests

  @property
  def mutex_groups(self):
    return self.data.mutex_groups

  @property
  def positional_args(self):
    return self.data.positional_args

  @property
  def flag_args(self):
    return self.data.flag_args

  @property
  def ancestor_flag_args(self):
    return self.data.ancestor_flag_args

  # pylint: disable=g-bad-name
  def add_argument(self, *args, **kwargs):
    """add_argument intercepts calls to the parser to track arguments."""
    # TODO(user): do not allow short-options without long-options.

    # we will choose the first option as the name
    name = args[0]

    positional = not name.startswith('-')
    if positional and not self.allow_positional:
      # TODO(user): More informative error message here about which group
      # the problem is in.
      raise ArgumentException('Illegal positional argument: ' + name)

    if positional and '-' in name:
      raise ArgumentException(
          "Positional arguments cannot contain a '-': " + name)

    dest = kwargs.get('dest')
    if not dest:
      # this is exactly what happens in argparse
      dest = name.lstrip(self.parser.prefix_chars).replace('-', '_')
    default = kwargs.get('default')
    required = kwargs.get('required')

    self.defaults[dest] = default
    if required:
      self.required.append(dest)
    self.dests.append(dest)
    if self.mutex_group_id:
      self.mutex_groups[dest] = self.mutex_group_id

    if positional and 'metavar' not in kwargs:
      kwargs['metavar'] = name.upper()

    added_argument = self.parser.add_argument(*args, **kwargs)

    if positional:
      self.positional_args.append(added_argument)
    else:
      self.flag_args.append(added_argument)

    return added_argument

  # pylint: disable=redefined-builtin
  def register(self, registry_name, value, object):
    return self.parser.register(registry_name, value, object)

  def set_defaults(self, **kwargs):
    return self.parser.set_defaults(**kwargs)

  def get_default(self, dest):
    return self.parser.get_default(dest)

  def add_argument_group(self, *args, **kwargs):
    new_parser = self.parser.add_argument_group(*args, **kwargs)
    return _ArgumentInterceptor(parser=new_parser,
                                allow_positional=self.allow_positional,
                                data=self.data)

  def add_mutually_exclusive_group(self, **kwargs):
    new_parser = self.parser.add_mutually_exclusive_group(**kwargs)
    return _ArgumentInterceptor(parser=new_parser,
                                allow_positional=self.allow_positional,
                                data=self.data,
                                mutex_group_id=id(new_parser))

  def AddFlagActionFromAncestors(self, action):
    """Add a flag action to this parser, but segregate it from the others.

    Segregating the action allows automatically generated help text to ignore
    this flag.

    Args:
      action: argparse.Action, The action for the flag being added.

    """
    # pylint:disable=protected-access, simply no other way to do this.
    self.parser._add_action(action)
    # explicitly do this second, in case ._add_action() fails.
    self.data.ancestor_flag_args.append(action)


class _ConfigHooks(object):
  """This class holds function hooks for context and config loading/saving."""

  def __init__(
      self,
      load_context=None,
      context_filters=None,
      group_class=None,
      load_config=None,
      save_config=None):
    """Create a new object with the given hooks.

    Args:
      load_context: a function that takes a config object and returns the
          context to be sent to commands.
      context_filters: a list of functions that take (contex, config, args),
          that will be called in order before a command is run. They are
          described in the README under the heading GROUP SPECIFICATION.
      group_class: base.Group, The class that this config hooks object is for.
      load_config: a zero-param function that returns the configuration
          dictionary to be sent to commands.
      save_config: a one-param function that takes a dictionary object and
          serializes it to a JSON file.
    """
    self.load_context = load_context if load_context else lambda cfg: {}
    self.context_filters = context_filters if context_filters else []
    self.group_class = group_class
    self.load_config = load_config if load_config else lambda: {}
    self.save_config = save_config if save_config else lambda cfg: None

  def OverrideWithBase(self, group_base):
    """Get a new _ConfigHooks object with overridden functions based on module.

    If module defines any of the function, they will be used instead of what
    is in this object.  Anything that is not defined will use the existing
    behavior.

    Args:
      group_base: The base.Group class corresponding to the group.

    Returns:
      A new _ConfigHooks object updated with any newly found hooks
    """

    def ContextFilter(context, config, args):
      group = group_base(config=config)
      group.Filter(context, args)
      return group
    # We want the new_context_filters to be a completely new list, if there is
    # a change.
    new_context_filters = self.context_filters + [ContextFilter]
    return _ConfigHooks(load_context=self.load_context,
                        context_filters=new_context_filters,
                        group_class=group_base,
                        load_config=self.load_config,
                        save_config=self.save_config)


class _CommandCommon(object):
  """A base class for _CommandGroup and _Command.

  It is responsible for extracting arguments from the modules and does argument
  validation, since this is always the same for groups and commands.
  """

  def __init__(self, module_dir, module_path, path, construction_id,
               config_hooks, help_func, parser_group, allow_positional_args,
               parent_group):
    """Create a new _CommandCommon.

    Args:
      module_dir: str, The path to the tools directory that this command or
          group lives within. Used to find the command or group's source file.
      module_path: [str], The command group names that brought us down to this
          command group or command from the top module directory.
      path: [str], Similar to module_path, but is the path to this command or
          group with respect to the CLI itself.  This path should be used for
          things like error reporting when a specific element in the tree needs
          to be referenced.
      construction_id: str, A unique identifier for the CLILoader that is
          being constructed.
      config_hooks: a _ConfigHooks object to use for loading/saving config.
      help_func: func([command path]), A function to call with --help.
      parser_group: argparse.Parser, The parser that this command or group will
          live in.
      allow_positional_args: bool, True if this command can have positional
          arguments.
      parent_group: _CommandGroup, The parent of this command or group. None if
          at the root.
    """
    module = self._GetModuleFromPath(module_dir, module_path, path,
                                     construction_id)

    self._help_func = help_func
    self._config_hooks = config_hooks
    self._parent_group = parent_group

    # pylint:disable=protected-access, The base module is effectively an
    # extension of calliope, and we want to leave _Common private so people
    # don't extend it directly.
    common_type = base._Common.FromModule(module)

    self.name = path[-1]
    # For the purposes of argparse and the help, we should use dashes.
    self.cli_name = self.name.replace('_', '-')
    path[-1] = self.cli_name
    self._module_path = module_path
    self._path = path
    self._construction_id = construction_id

    self._common_type = common_type
    self._common_type.group_class = config_hooks.group_class

    (self.short_help, self.long_help) = usage_text.ExtractHelpStrings(
        self._common_type.__doc__)

    self.detailed_help = getattr(self._common_type, 'detailed_help', {})

    self._AssignParser(
        parser_group=parser_group,
        help_func=help_func,
        allow_positional_args=allow_positional_args)

  def _AssignParser(self, parser_group, help_func, allow_positional_args):
    """Assign a parser group to model this Command or CommandGroup.

    Args:
      parser_group: argparse._ArgumentGroup, the group that will model this
          command or group's arguments.
      help_func: func([str]), The long help function that is used for --help.
      allow_positional_args: bool, Whether to allow positional args for this
          group or not.

    """
    if not parser_group:
      # This is the root of the command tree, so we create the first parser.
      self._parser = argparse.ArgumentParser(description=self.long_help,
                                             add_help=False,
                                             prog='.'.join(self._path))
    else:
      # This is a normal sub group, so just add a new subparser to the existing
      # one.
      self._parser = parser_group.add_parser(
          self.cli_name,
          help=self.short_help,
          description=self.long_help,
          add_help=False,
          prog='.'.join(self._path))

    # pylint:disable=protected-access
    self._parser._check_value = usage_text.CheckValueAndSuggest
    self._parser.error = usage_text.PrintParserError(self._parser)

    self._sub_parser = None

    self._ai = _ArgumentInterceptor(
        parser=self._parser,
        allow_positional=allow_positional_args)

    self._short_help_action = actions.ShortHelpAction(self, self._ai)

    if help_func:
      self._ai.add_argument(
          '-h', action=self._short_help_action,
          help='Print a summary help and exit.')
      def LongHelp():
        help_func(
            self._path,
            default=usage_text.ShortHelpText(self, self._ai))
      self._ai.add_argument(
          '--help', action=actions.FunctionExitAction(LongHelp),
          help='Display detailed help.')
    else:
      self._ai.add_argument(
          '-h', '--help', action=self._short_help_action,
          help='Print a summary help and exit.')


    self._AcquireArgs()

  def GetPath(self):
    return self._path

  def GetDocString(self):
    if self.long_help:
      return self.long_help
    if self.short_help:
      return self.short_help
    return 'The {name} command.'.format(name=self.name)

  def GetShortHelp(self):
    return usage_text.ShortHelpText(self, self._ai)

  def GetSubCommandHelps(self):
    return {}

  def GetSubGroupHelps(self):
    return {}

  def _GetModuleFromPath(self, module_dir, module_path, path, construction_id):
    """Import the module and dig into it to return the namespace we are after.

    Import the module relative to the top level directory.  Then return the
    actual module corresponding to the last bit of the path.

    Args:
      module_dir: str, The path to the tools directory that this command or
        group lives within.
      module_path: [str], The command group names that brought us down to this
        command group or command from the top module directory.
      path: [str], The same as module_path but with the groups named as they
        will be in the CLI.
      construction_id: str, A unique identifier for the CLILoader that is
        being constructed.

    Returns:
      The imported module.
    """
    src_dir = os.path.join(module_dir, *module_path[:-1])
    f = None
    m = imp.find_module(module_path[-1], [src_dir])
    f, file_path, items = m
    # Make sure this module name never collides with any real module name.
    # Use the CLI naming path, so values are always unique.
    name = '__calliope__command__.{construction_id}.{name}'.format(
        construction_id=construction_id,
        name='.'.join(path).replace('-', '_'))
    try:
      module = imp.load_module(name, f, file_path, items)
    # pylint:disable=broad-except, We really do want to catch everything here,
    # because if any exceptions make it through for any single command or group
    # file, the whole CLI will not work. Instead, just log whatever it is.
    except Exception as e:
      _, _, exc_traceback = sys.exc_info()
      raise CommandLoadFailure('.'.join(path), e), None, exc_traceback
    finally:
      if f:
        f.close()
    return module

  def _AcquireArgs(self):
    """Call the function to register the arguments for this module."""
    args_func = self._common_type.Args
    if not args_func:
      return
    args_func(self._ai)

    if self._parent_group:
      # Add parent flags to children, if they aren't represented already
      for flag in self._parent_group.GetAllAvailableFlags():
        if flag.option_strings in [['-h'], ['--help'], ['-h', '--help']]:
          # Each command or group gets its own unique help flags.
          continue
        if flag.required:
          # It is not easy to replicate required flags to subgroups and
          # subcommands, since then there would be two+ identical required
          # flags, and we'd want only one of them to be necessary.
          continue
        try:
          self._ai.AddFlagActionFromAncestors(flag)
        except argparse.ArgumentError:
          raise ArgumentException(
              'repeated flag in {command}: {flag}'.format(
                  command='.'.join(self._path),
                  flag=flag.option_strings))

  def GetAllAvailableFlags(self):
    return self._ai.flag_args + self._ai.ancestor_flag_args

  def _GetSubPathsForNames(self, names):
    """Gets a list of (module path, path) for the given list of sub names.

    Args:
      names: The names of the sub groups or commands the paths are for

    Returns:
      A list of tuples of the new (module_path, path) for the given names.
      These terms are that as used by the constructor of _CommandGroup and
      _Command.
    """
    return [(self._module_path + [name], self._path + [name]) for name in names]

  def Parser(self):
    """Return the argparse parser this group is using.

    Returns:
      The argparse parser this group is using
    """
    return self._parser

  def SubParser(self):
    """Gets or creates the argparse sub parser for this group.

    Returns:
      The argparse subparser that children of this group should register with.
          If a sub parser has not been allocated, it is created now.
    """
    if not self._sub_parser:
      self._sub_parser = self._parser.add_subparsers()
    return self._sub_parser

  def CreateNewArgs(self, kwargs, current_args, cli_mode):
    """Make a new argument dictionary from default, existing, and new args.

    Args:
      kwargs: The keyword args the user provided for this level
      current_args: The arguments that have previously been collected at other
          levels
      cli_mode: True if we are doing arg parsing for cli mode.

    Returns:
      A new argument dictionary
    """
    if cli_mode:
      # We are binding one big dictionary of arguments.  Filter out all the
      # arguments that don't belong to this level.
      filtered_kwargs = {}
      for key, value in kwargs.iteritems():
        if key in self._ai.dests:
          filtered_kwargs[key] = value
      kwargs = filtered_kwargs

    # Make sure the args provided at this level are OK.
    self._ValidateArgs(kwargs, cli_mode)
    # Start with the defaults arguments for this level.
    new_args = dict(self._ai.defaults)
    # Add in anything that was already collected above us in the tree.
    new_args.update(current_args)
    # Add in the args from this invocation.
    new_args.update(kwargs)
    return new_args

  def _ValidateArgs(self, args, cli_mode):
    """Make sure the given arguments are correct for this level.

    Ensures that any required args are provided as well as that no unexpected
    arguments were provided.

    Args:
      args:  A dictionary of the arguments that were provided
      cli_mode: True if we are doing arg parsing for cli mode.

    Raises:
      ArgumentException: If mutually exclusive arguments were both given.
      MissingArgumentException: If there are missing required arguments.
      UnexpectedArgumentException: If there are unexpected arguments.
    """
    missed_args = []
    for required in self._ai.required:
      if required not in args:
        missed_args.append(required)
    if missed_args:
      raise MissingArgumentException(self._path, missed_args)

    unexpected_args = []
    for dest in args:
      if dest not in self._ai.dests:
        unexpected_args.append(dest)
    if unexpected_args:
      raise UnexpectedArgumentException(self._path, unexpected_args)

    if not cli_mode:
      # We only need to do mutex group detections when binding args manually.
      # Argparse will take care of this when on the CLI.
      found_groups = {}
      group_ids = self._ai.mutex_groups
      for dest in sorted(args):
        group_id = group_ids.get(dest)
        if group_id:
          found = found_groups.get(group_id)
          if found:
            raise ArgumentException('Argument {0} is not allowed with {1}'
                                    .format(dest, found))
          found_groups[group_id] = dest


class _CommandGroup(_CommandCommon):
  """A class to encapsulate a group of commands."""

  def __init__(self, module_dir, module_path, path, construction_id,
               parser_group, config_hooks, help_func, parent_group=None):
    """Create a new command group.

    Args:
      module_dir: always the root of the whole command tree
      module_path: a list of command group names that brought us down to this
          command group from the top module directory
      path: similar to module_path, but is the path to this command group
          with respect to the CLI itself.  This path should be used for things
          like error reporting when a specific element in the tree needs to be
          referenced
      construction_id: str, A unique identifier for the CLILoader that is
          being constructed.
      parser_group: the current argparse parser, or None if this is the root
          command group.  The root command group will allocate the initial
          top level argparse parser.
      config_hooks: a _ConfigHooks object to use for loading/saving config
      help_func: func([command path]), A function to call with --help.
      parent_group: _CommandGroup, The parent of this group. None if at the
          root.

    Raises:
      LayoutException: if the module has no sub groups or commands
    """

    super(_CommandGroup, self).__init__(
        module_dir=module_dir,
        module_path=module_path,
        path=path,
        construction_id=construction_id,
        config_hooks=config_hooks,
        help_func=help_func,
        allow_positional_args=False,
        parser_group=parser_group,
        parent_group=parent_group)

    self._module_dir = module_dir

    self._LoadSubGroups()

    self._parser.usage = usage_text.GenerateUsage(self, self._ai)
    self._parser.error = usage_text.PrintShortHelpError(self._parser, self)

  def _LoadSubGroups(self):
    """Load all of this group's subgroups and commands."""
    self._config_hooks = self._config_hooks.OverrideWithBase(self._common_type)

    # find sub groups and commands
    self.groups = []
    self.commands = []
    (group_names, command_names) = self._FindSubGroups()
    self.all_sub_names = set(group_names + command_names)
    if not group_names and not command_names:
      raise LayoutException('Group %s has no subgroups or commands'
                            % '.'.join(self._path))

    # recursively create the tree of command groups and commands
    sub_parser = self.SubParser()
    for (new_module_path, new_path) in self._GetSubPathsForNames(group_names):
      self.groups.append(
          _CommandGroup(self._module_dir, new_module_path, new_path,
                        self._construction_id, sub_parser, self._config_hooks,
                        help_func=self._help_func,
                        parent_group=self))

    for (new_module_path, new_path) in self._GetSubPathsForNames(command_names):
      cmd = _Command(self._module_dir, new_module_path, new_path,
                     self._construction_id, self._config_hooks, sub_parser,
                     self._help_func, parent_group=self)
      self.commands.append(cmd)

  def MakeShellActions(self, loader):
    group_names = [group.name.replace('_', '-') for group in self.groups]
    command_names = [command.name.replace('_', '-')
                     for command in self.commands]
    self._ai.add_argument(
        '--shell',
        action=shell.ShellAction(group_names + command_names, loader),
        nargs='?',
        help=argparse.SUPPRESS)
    for group in self.groups:
      group.MakeShellActions(loader)

  def GetSubCommandHelps(self):
    return dict((item.cli_name, item.short_help or '')
                for item in self.commands)

  def GetSubGroupHelps(self):
    return dict((item.cli_name, item.short_help or '')
                for item in self.groups)

  def GetHelpFunc(self):
    return self._help_func

  def AddSubGroup(self, group):
    """Merges another command group under this one.

    If we load command groups for alternate locations, this method is used to
    make those extra sub groups fall under this main group in the CLI.

    Args:
      group: Any other _CommandGroup object that should be added to the CLI
    """
    self.groups.append(group)
    self.all_sub_names.add(group.name)
    self._parser.usage = usage_text.GenerateUsage(self, self._ai)

  def IsValidSubName(self, name):
    """See if the given name is a name of a registered sub group or command.

    Args:
      name: The name to check

    Returns:
      True if the given name is a registered sub group or command of this
      command group.
    """
    return name in self.all_sub_names

  def _FindSubGroups(self):
    """Final all the sub groups and commands under this group.

    Returns:
      A tuple containing two lists. The first is a list of strings for each
      command group, and the second is a list of strings for each command.

    Raises:
      LayoutException: if there is a command or group with an illegal name.
    """
    location = os.path.join(self._module_dir, *self._module_path)
    items = os.listdir(location)
    groups = []
    commands = []
    items.sort()
    for item in items:
      name, ext = os.path.splitext(item)
      itempath = os.path.join(location, item)

      if ext == '.py':
        if name == '__init__':
          continue
      elif not os.path.isdir(itempath):
        continue

      if re.search('[A-Z]', name):
        raise LayoutException('Commands and groups cannot have capital letters:'
                              ' %s.' % name)

      if not os.path.isdir(itempath):
        commands.append(name)
      else:
        init_path = os.path.join(itempath, '__init__.py')
        if os.path.exists(init_path):
          groups.append(item)
    return groups, commands


class _Command(_CommandCommon):
  """A class that encapsulates the configuration for a single command."""

  def __init__(self, module_dir, module_path, path, construction_id,
               config_hooks, parser_group, help_func, parent_group=None):
    """Create a new command.

    Args:
      module_dir: str, The root of the command tree.
      module_path: a list of command group names that brought us down to this
          command from the top module directory
      path: similar to module_path, but is the path to this command with respect
          to the CLI itself.  This path should be used for things like error
          reporting when a specific element in the tree needs to be referenced
      construction_id: str, A unique identifier for the CLILoader that is
          being constructed.
      config_hooks: a _ConfigHooks object to use for loading/saving config
      parser_group: argparse.Parser, The parser to be used for this command.
      help_func: func([str]), Detailed help function.
      parent_group: _CommandGroup, The parent of this command.
    """
    super(_Command, self).__init__(
        module_dir=module_dir,
        module_path=module_path,
        path=path,
        construction_id=construction_id,
        config_hooks=config_hooks,
        help_func=help_func,
        allow_positional_args=True,
        parser_group=parser_group,
        parent_group=parent_group)

    self._parser.set_defaults(cmd_func=self.Run, command_path=self._path)

    self._parser.usage = usage_text.GenerateUsage(self, self._ai)

  def Run(self, args, command=None, cli_mode=False, pre_run_hooks=None,
          post_run_hooks=None):
    """Run this command with the given arguments.

    Args:
      args: The arguments for this command as a namespace.
      command: The bound Command object that is used to run this _Command.
      cli_mode: bool, True if running from the command line, False if running
        interactively.
      pre_run_hooks: [_RunHook], Things to run before the command.
      post_run_hooks: [_RunHook], Things to run after the command.

    Returns:
      The object returned by the module's Run() function.

    Raises:
      exceptions.Error: if thrown by the Run() function.
    """
    command_path_string = '.'.join(self._path)

    properties.VALUES.PushArgs(args)
    # Enable user output for CLI mode only if it is not explicitly set in the
    # properties (or given in the provided arguments that were just pushed into
    # the properties object).
    user_output_enabled = properties.VALUES.core.user_output_enabled.GetBool()
    set_user_output_property = cli_mode and user_output_enabled is None
    if set_user_output_property:
      properties.VALUES.core.user_output_enabled.Set(True)
    # Now that we have pushed the args, reload the settings so the flags will
    # take effect.  These will use the values from the properties.
    old_user_output_enabled = log.SetUserOutputEnabled(None)
    old_verbosity = log.SetVerbosity(None)

    try:
      if cli_mode and pre_run_hooks:
        for hook in pre_run_hooks:
          hook.Run(command_path_string)

      config = self._config_hooks.load_config()
      tool_context = self._config_hooks.load_context(config)
      last_group = None
      for context_filter in self._config_hooks.context_filters:
        last_group = context_filter(tool_context, config, args)

      command_instance = self._common_type(
          context=tool_context,
          config=config,
          entry_point=command.EntryPoint(),
          command=command,
          group=last_group)
      log.debug('Running %s with %s.', command_path_string, args)
      result = command_instance.Run(args)
      self._config_hooks.save_config(config)
      command_instance.Display(args, result)

      if cli_mode and post_run_hooks:
        for hook in post_run_hooks:
          hook.Run(command_path_string)

      return result

    except core_exceptions.Error as exc:
      msg = '({0}) {1}'.format(command_path_string, str(exc))
      log.debug(msg, exc_info=sys.exc_info())
      if cli_mode:
        log.error(msg)
        sys.exit(1)
      else:
        raise
    except Exception as exc:
      # Make sure any uncaught exceptions still make it into the log file.
      log.file_only_logger.debug(str(exc), exc_info=sys.exc_info())
      raise
    finally:
      if set_user_output_property:
        properties.VALUES.core.user_output_enabled.Set(None)
      log.SetUserOutputEnabled(old_user_output_enabled)
      log.SetVerbosity(old_verbosity)
      properties.VALUES.PopArgs()


class UnboundCommandGroup(object):
  """A class to represent an unbound command group in the REPL.

  Unbound refers to the fact that no arguments have been bound to this command
  group yet.  This object can be called with a set of arguments to set them.
  You can also access any sub group or command of this group as a property if
  this group does not require any arguments at this level.
  """

  def __init__(self, parent_group, group):
    """Create a new UnboundCommandGroup.

    Args:
      parent_group: The BoundCommandGroup this is a descendant of or None if
          this is the root command.
      group: The _CommandGroup that this object is representing
    """
    self._parent_group = parent_group
    self._group = group

    # We change the .__doc__ so that when calliope is used in interpreter mode,
    # the user can inspect .__doc__ and get the help messages provided by the
    # tool creator.
    self.__doc__ = self._group.GetDocString()

  def ParentGroup(self):
    """Gives you the bound command group this group is a descendant of.

    Returns:
      The BoundCommandGroup above this one in the tree or None if we are the top
    """
    return self._parent_group

  def GetShortHelp(self):
    return self._group.GetShortHelp()

  def __call__(self, **kwargs):
    return self._BindArgs(kwargs=kwargs, cli_mode=False)

  def _BindArgs(self, kwargs, cli_mode):
    """Bind arguments to this command group.

    This is called with the kwargs to bind to this command group.  It validates
    that the group has registered the provided args and that any required args
    are provided.

    Args:
      kwargs: The args to bind to this command group.
      cli_mode: True if we are doing arg parsing for cli mode.

    Returns:
      A new BoundCommandGroup with the given arguments
    """
    # pylint: disable=protected-access, We don't want to expose the member or an
    # accessor since this is a user facing class.  These three classes all work
    # as a single unit.
    current_args = self._parent_group._args if self._parent_group else {}
    # Compute the new argument bindings for what was just provided.
    new_args = self._group.CreateNewArgs(
        kwargs=kwargs,
        current_args=current_args,
        cli_mode=cli_mode)

    bound_group = BoundCommandGroup(self, self._group, self._parent_group,
                                    new_args, kwargs)
    return bound_group

  def __getattr__(self, name):
    """Access sub groups or commands without using () notation.

    Accessing a sub group or command without using the above call, implicitly
    executes the binding with no arguments.  If the context has required
    arguments, this will fail.

    Args:
      name: the name of the attribute to get

    Returns:
      A new UnboundCommandGroup or Command created by binding this command group
      with no arguments.

    Raises:
      AttributeError: if the given name is not a valid sub group or command
    """
    # Map dashes in the CLI to underscores in the API.
    name = name.replace('-', '_')
    if self._group.IsValidSubName(name):
      # Bind zero arguments to this group and then get the name we actually
      # asked for
      return getattr(self._BindArgs(kwargs={}, cli_mode=False), name)
    raise AttributeError(name)

  def Name(self):
    return self._group.name

  def HelpFunc(self):
    return self._group.GetHelpFunc()

  def __repr__(self):
    s = ''
    if self._parent_group:
      s += '%s.' % repr(self._parent_group)
    s += self.Name()
    return s


class BoundCommandGroup(object):
  """A class to represent a bound command group in the REPL.

  Bound refers to the fact that arguments have already been provided for this
  command group.  You can access sub groups or commands of this group as
  properties.
  """

  def __init__(self, unbound_group, group, parent_group, args, new_args):
    """Create a new BoundCommandGroup.

    Args:
      unbound_group: the UnboundCommandGroup that this BoundCommandGroup was
          created from.
      group: The _CommandGroup equivalent for this group.
      parent_group: The BoundCommandGroup this is a descendant of
      args: All the default and provided arguments from above and including
          this group.
      new_args: The args used to bind this command group, not including those
          from its parent groups.
    """
    self._unbound_group = unbound_group
    self._group = group
    self._parent_group = parent_group
    self._args = args
    self._new_args = new_args
    # Create attributes for each sub group or command that can come next.
    for group in self._group.groups:
      setattr(self, group.name, UnboundCommandGroup(self, group))
    for command in self._group.commands:
      setattr(self, command.name, Command(self, command))

    self.__doc__ = self._group.GetDocString()

  def __getattr__(self, name):
    # Map dashes in the CLI to underscores in the API.
    fixed_name = name.replace('-', '_')
    if name == fixed_name:
      raise AttributeError
    return getattr(self, fixed_name)

  def UnboundGroup(self):
    return self._unbound_group

  def ParentGroup(self):
    """Gives you the bound command group this group is a descendant of.

    Returns:
      The BoundCommandGroup above this one in the tree or None if we are the top
    """
    return self._parent_group

  def GetShortHelp(self):
    return self._group.GetShortHelp()

  def __repr__(self):
    s = ''
    if self._parent_group:
      s += '%s.' % repr(self._parent_group)
    s += self._group.name

    # There are some things in the args which are set by default, like cmd_func
    # and command_path, which should not appear in the repr.
    # pylint:disable=protected-access
    valid_args = self._group._ai.dests
    args = ', '.join(['{0}={1}'.format(arg, repr(val))
                      for arg, val in self._new_args.iteritems()
                      if arg in valid_args])
    if args:
      s += '(%s)' % args
    return s


class Command(object):
  """A class representing a command that can be called in the REPL.

  At this point, contexts about this command have already been created and bound
  to any required arguments for those command groups.  This object can be called
  to actually invoke the underlying command.
  """

  def __init__(self, parent_group, command):
    """Create a new Command.

    Args:
      parent_group: The BoundCommandGroup this is a descendant of
      command: The _Command object to actually invoke
    """
    self._parent_group = parent_group
    self._command = command

    # We change the .__doc__ so that when calliope is used in interpreter mode,
    # the user can inspect .__doc__ and get the help messages provided by the
    # tool creator.
    self.__doc__ = self._command.GetDocString()

  def ParentGroup(self):
    """Gives you the bound command group this group is a descendant of.

    Returns:
      The BoundCommandGroup above this one in the tree or None if we are the top
    """
    return self._parent_group

  def __call__(self, **kwargs):
    return self._Execute(cli_mode=False, pre_run_hooks=None,
                         post_run_hooks=None, kwargs=kwargs)

  def GetShortHelp(self):
    return self._command.GetShortHelp()

  def EntryPoint(self):
    """Get the entry point that owns this command."""

    cur = self
    while cur.ParentGroup():
      cur = cur.ParentGroup()
    if type(cur) is BoundCommandGroup:
      cur = cur.UnboundGroup()
    return cur

  def _Execute(self, cli_mode, pre_run_hooks, post_run_hooks, kwargs):
    """Invoke the underlying command with the given arguments.

    Args:
      cli_mode: If true, run in CLI mode without checking kwargs for validity.
      pre_run_hooks: [_RunHook], Things to run before the command.
      post_run_hooks: [_RunHook], Things to run after the command.
      kwargs: The arguments with which to invoke the command.

    Returns:
      The result of executing the command determined by the command
      implementation
    """
    # pylint: disable=protected-access, We don't want to expose the member or an
    # accessor since this is a user facing class.  These three classes all work
    # as a single unit.
    parent_args = self._parent_group._args if self._parent_group else {}
    new_args = self._command.CreateNewArgs(
        kwargs=kwargs,
        current_args=parent_args,
        cli_mode=cli_mode)  # we ignore unknown when in cli mode
    arg_namespace = _Args(new_args)
    return self._command.Run(
        args=arg_namespace, command=self, cli_mode=cli_mode,
        pre_run_hooks=pre_run_hooks, post_run_hooks=post_run_hooks)

  def __repr__(self):
    s = ''
    if self._parent_group:
      s += '%s.' % repr(self._parent_group)
    s += self._command.name
    return s


class _RunHook(object):
  """Encapsulates a function to be run before or after command execution."""

  def __init__(self, func, include_commands=None, exclude_commands=None):
    """Constructs the hook.

    Args:
      func: function, The no args function to run.
      include_commands: str, A regex for the command paths to run.  If not
        provided, the hook will be run for all commands.
      exclude_commands: str, A regex for the command paths to exclude.  If not
        provided, nothing will be excluded.
    """
    self.__func = func
    self.__include_commands = include_commands if include_commands else '.*'
    self.__exclude_commands = exclude_commands

  def Run(self, command_path):
    """Runs this hook if the filters match the given command.

    Args:
      command_path: str, The calliope command path for the command that was run.

    Returns:
      bool, True if the hook was run, False if it did not match.
    """
    if not re.match(self.__include_commands, command_path):
      return False
    if self.__exclude_commands and re.match(self.__exclude_commands,
                                            command_path):
      return False
    self.__func()
    return True


class CLILoader(object):
  """A class to encapsulate loading the CLI and bootstrapping the REPL."""

  # Splits a path like foo.bar.baz into 2 groups: foo.bar, and baz.  Group 1 is
  # optional.
  PATH_RE = r'(?:([\w\.]+)\.)?([^\.]+)'

  def __init__(self, name, command_root_directory,
               allow_non_existing_modules=False, load_context=None,
               config_file=None, logs_dir=None, version_func=None,
               help_func=None):
    """Initialize Calliope.

    Args:
      name: str, The name of the top level command, used for nice error
        reporting.
      command_root_directory: str, The path to the directory containing the main
        CLI module.
      allow_non_existing_modules: True to allow extra module directories to not
        exist, False to raise an exception if a module does not exist.
      load_context: A function that takes the persistent config dict as a
        parameter and returns a context dict, or None for a default which
        always returns {}.
      config_file: str, A path to a config file to use for json config
        loading/saving, or None to disable config.
      logs_dir: str, The path to the root directory to store logs in, or None
        for no log files.
      version_func: func, A function to call for a top-level -v and
        --version flag. If None, no flags will be available.
      help_func: func([command path]), A function to call for in-depth help
        messages. It is passed the set of subparsers used (not including the
        top-level command). After it is called calliope will exit. This function
        will be called when a top-level 'help' command is run, or when the
        --help option is added on to any command.

    Raises:
      LayoutException: If no command root directory is given.
    """
    self.__name = name
    self.__command_root_directory = command_root_directory
    if not self.__command_root_directory:
      raise LayoutException('You must specify a command root directory.')

    self.__allow_non_existing_modules = allow_non_existing_modules

    self.__config_file = config_file
    self.__config_hooks = _ConfigHooks(
        load_context=load_context,
        load_config=self.__CreateLoadConfigFunction(),
        save_config=self.__CreateSaveConfigFunction())
    self.__logs_dir = logs_dir
    self.__version_func = version_func
    self.__help_func = help_func

    self.__pre_run_hooks = []
    self.__post_run_hooks = []

    self.__top_level_command = None
    self.__modules = []

  def __CreateLoadConfigFunction(self):
    """Generates a function that loads config from a file if it is set.

    Returns:
      The function to load the configuration or None
    """
    if not self.__config_file:
      return None
    def _LoadConfig():
      if os.path.exists(self.__config_file):
        with open(self.__config_file) as cfile:
          cfgdict = json.load(cfile)
          if cfgdict:
            return cfgdict
      return {}
    return _LoadConfig

  def __CreateSaveConfigFunction(self):
    """Generates a function that saves config from a file if it is set.

    Returns:
      The function to save the configuration or None
    """
    if not self.__config_file:
      return None
    def _SaveConfig(cfg):
      """Save the config to the correct file."""
      config_dir, _ = os.path.split(self.__config_file)
      try:
        if not os.path.isdir(config_dir):
          os.makedirs(config_dir)
      except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(config_dir):
          pass
        else: raise

      with open(self.__config_file, 'w') as cfile:
        json.dump(cfg, cfile, indent=2)
        cfile.write('\n')
    return _SaveConfig

  def SetTopLevelCommand(self, name):
    """Sets the name of the top level command for single command CLIs.

    If you are making a CLI with no subgroups, use this to set the name of the
    command to use from the command root directory.

    Args:
      name: str, The name of the command to add.  This must correspond to a
        <name>.py file in the command root directory.

    Raises:
      LayoutException: If modules have already been added.
    """
    if self.__modules:
      raise LayoutException(
          'You cannot set a top level command because command modules have '
          'already been added.')
    self.__top_level_command = name

  def AddModule(self, name, path):
    """Adds a module to this CLI tool.

    If you are making a CLI that has subgroups, use this to add in more
    directories of commands.

    Args:
      name: str, The name of the group to create under the main CLI.  If this is
        to be placed under another group, a dotted name can be used.
      path: str, The full path the directory containing the commands for this
        group.

    Raises:
      LayoutException: If a top level command has already been added.
    """
    if self.__top_level_command:
      raise LayoutException(
          'You cannot add a module because a top level command has already '
          'been set.')
    self.__modules.append((name, path))

  def RegisterPreRunHook(self, func,
                         include_commands=None, exclude_commands=None):
    """Register a function to be run before command execution.

    Args:
      func: function, The no args function to run.
      include_commands: str, A regex for the command paths to run.  If not
        provided, the hook will be run for all commands.
      exclude_commands: str, A regex for the command paths to exclude.  If not
        provided, nothing will be excluded.
    """
    hook = _RunHook(func, include_commands, exclude_commands)
    self.__pre_run_hooks.append(hook)

  def RegisterPostRunHook(self, func,
                          include_commands=None, exclude_commands=None):
    """Register a function to be run after command execution.

    Args:
      func: function, The no args function to run.
      include_commands: str, A regex for the command paths to run.  If not
        provided, the hook will be run for all commands.
      exclude_commands: str, A regex for the command paths to exclude.  If not
        provided, nothing will be excluded.
    """
    hook = _RunHook(func, include_commands, exclude_commands)
    self.__post_run_hooks.append(hook)

  def Generate(self):
    """Uses the registered information to generate the CLI tool.

    Returns:
      CLI, The generated CLI tool.
    """
    if self.__top_level_command:
      return self.__LoadCLIFromSingleCommand()
    return self.__LoadCLIFromGroups()

  def __LoadCLIFromSingleCommand(self):
    """Load the CLI from a single command.

    When loaded for a single command, there are no groups and no global
    arguments.  This is use when a calliope command needs to be made a
    standalone command.

    Raises:
      LayoutException: If the top level command file does not exist.

    Returns:
      CLI, The generated CLI tool.
    """
    if not self.__top_level_command:
      raise LayoutException('No top level command registered.')
    file_path = os.path.join(self.__command_root_directory,
                             self.__top_level_command + '.py')
    if not os.path.isfile(file_path):
      raise LayoutException(
          'The given command does not exist: {}'.format(file_path))
    top_command = _Command(
        self.__command_root_directory, [self.__top_level_command],
        [self.__name], uuid.uuid4().hex, self.__config_hooks, parser_group=None,
        help_func=self.__help_func)
    parser = top_command.Parser()
    entry_point = Command(None, top_command)

    return self.__MakeCLI(entry_point, parser, top_command)

  def __LoadCLIFromGroups(self):
    """Load the CLI from a command directory.

    Returns:
      CLI, The generated CLI tool.
    """
    top_group = self.__LoadGroup(self.__command_root_directory, None,
                                 allow_non_existing_modules=False)
    registered_groups = {None: top_group}
    self.__RegisterAllSubGroups(top_group, registered_groups)

    for module_dot_path, module_dir in self.__modules:
      try:
        match = re.match(CLILoader.PATH_RE, module_dot_path)
        root, name = match.group(1, 2)
        parent_group = registered_groups.get(root)
        exception_if_present = None
        if not parent_group:
          exception_if_present = LayoutException(
              'Root [{root}] for command group [{group}] does not exist.'
              .format(root=root, group=name))

        path_list = module_dot_path.split('.')
        group = self.__LoadGroup(
            module_dir, parent_group, module_path=path_list,
            allow_non_existing_modules=self.__allow_non_existing_modules,
            exception_if_present=exception_if_present, top_group=top_group)
        if group:
          self.__RegisterAllSubGroups(group, registered_groups)
          parent_group.AddSubGroup(group)
      except CommandLoadFailure as e:
        log.exception(e)

    parser = top_group.Parser()
    entry_point = UnboundCommandGroup(None, top_group)
    cli = self.__MakeCLI(entry_point, parser, top_group)
    top_group.MakeShellActions(cli)

    return cli

  def __RegisterAllSubGroups(self, group, registered_groups):
    for g in self.__GetAllGroups(group):
      # pylint: disable=protected-access
      registered_groups['.'.join(g._path[1:])] = g

  def __GetAllGroups(self, starting_group, groups=None):
    if not groups:
      groups = []
    groups.append(starting_group)
    for g in starting_group.groups:
      self.__GetAllGroups(g, groups)
    return groups

  def __LoadGroup(self, module_directory, parent_group, module_path=None,
                  allow_non_existing_modules=False, exception_if_present=None,
                  top_group=None):
    """Loads a single command group from a directory.

    Args:
      module_directory: The path to the location of the module
      parent_group: _CommandGroup, The parent command group for this command
        group, or None if this is the top group.
      module_path: An optional name override for the module. If not set, it will
        default to using the name of the directory containing the module.
      allow_non_existing_modules: True to allow this module directory to not
        exist, False to raise an exception if this module does not exist.
      exception_if_present: Exception, An exception to throw if the module
        actually exists, or None.
      top_group: _CommandGroup, The top command group for this CLI.

    Raises:
      LayoutException: If the module directory does not exist and
      allow_non_existing is False.

    Returns:
      The _CommandGroup object, or None if the module directory does not exist
      and allow_non_existing is True.
    """
    if not os.path.isdir(module_directory):
      if allow_non_existing_modules:
        return None
      raise LayoutException('The given module directory does not exist: {}'
                            .format(module_directory))
    elif exception_if_present:
      # pylint: disable=raising-bad-type, This will be an actual exception.
      raise exception_if_present

    module_root, module = os.path.split(module_directory)
    if not module_path:
      module_path = [module]
    # If this is the top level, don't register the name of the module directory
    # itself, it should assume the name of the command.  If this is another
    # module directory, its name gets explicitly registered under the root
    # command.
    is_top = not parent_group
    sub_parser = parent_group.SubParser() if parent_group else None
    path = [self.__name] if is_top else [self.__name] + module_path
    group = _CommandGroup(
        module_root, [module], path, uuid.uuid4().hex, sub_parser,
        self.__config_hooks, help_func=self.__help_func,
        parent_group=top_group)

    return group

  def __MakeCLI(self, entry_point, parser, top_element):
    """Generate a CLI object from the given data.

    Args:
      entry_point: The REPL entrypoint for this CLI.
      parser: The argparse parser for the top of this command tree.
      top_element: The top element of the command tree
        (that extends _CommandCommon).

    Returns:
      CLI, The generated CLI tool.
    """
    if self.__version_func is not None:
      parser.add_argument(
          '-v', '--version',
          action=actions.FunctionExitAction(self.__version_func),
          help='Print version information.')
    # pylint: disable=protected-access
    top_element._ai.add_argument(
        '--verbosity',
        choices=log.OrderedVerbosityNames(),
        default=None,
        help='Override the default verbosity for this command.  This must be '
        'a standard logging verbosity level: [{values}] (Default: [{default}]).'
        .format(values=', '.join(log.OrderedVerbosityNames()),
                default=log.DEFAULT_VERBOSITY_STRING))
    top_element._ai.add_argument(
        '--user-output-enabled',
        default=None,
        choices=('true', 'false'),
        help='Control whether user intended output is printed to the console.  '
        '(true/false)')

    if '_ARGCOMPLETE' not in os.environ:
      # Don't bother setting up logging if we are just doing a completion.
      log.AddFileLogging(self.__logs_dir)

    return CLI(entry_point, parser, self.__pre_run_hooks, self.__post_run_hooks)


class CLI(object):
  """A generated command line tool."""

  def __init__(self, entry_point, parser, pre_run_hooks, post_run_hooks):
    self.__entry_point = entry_point
    self.__parser = parser
    self.__pre_run_hooks = pre_run_hooks
    self.__post_run_hooks = post_run_hooks
    self.args = []

  def _ArgComplete(self):
    argcomplete.autocomplete(self.__parser, always_complete_options=False)

  def Execute(self, args=None):
    """Execute the CLI tool with the given arguments.

    Args:
      args: The arguments from the command line or None to use sys.argv
    """
    self._ArgComplete()

    self.argv = args or sys.argv[1:]
    args = self.__parser.parse_args(self.argv)
    command_path_string = '.'.join(args.command_path)

    # TODO(user): put a real version here
    metrics.Commands(command_path_string, None)
    path = args.command_path[1:]
    kwargs = args.__dict__

    # Dig down into the groups and commands, binding the arguments at each step.
    # If the path is empty, this means that we have an actual command as the
    # entry point and we don't need to dig down, just call it directly.

    # The command_path will be, eg, ['top', 'group1', 'group2', 'command'], and
    # is set by each _Command when it's loaded from
    # 'tools/group1/group2/command.py'. It corresponds also to the python object
    # built to mirror the command line, with 'top' corresponding to the
    # entry point returned by the EntryPoint() method. Then, in this case, the
    # object found with self.EntryPoint().group1.group2.command is the runnable
    # command being targetted by this operation. The following code segment
    # does this digging and applies the relevant arguments at each step, taken
    # from the argparse results.

    # pylint: disable=protected-access
    cur = self.EntryPoint()
    while path:
      cur = cur._BindArgs(kwargs=kwargs, cli_mode=True)
      cur = getattr(cur, path[0])
      path = path[1:]

    cur._Execute(cli_mode=True, pre_run_hooks=self.__pre_run_hooks,
                 post_run_hooks=self.__post_run_hooks, kwargs=kwargs)

  def EntryPoint(self):
    """Get the top entry point into the REPL for interactive mode.

    Returns:
      A REPL command group that allows you to bind args and call commands
      interactively in the same way you would from the command line.
    """
    return self.__entry_point
