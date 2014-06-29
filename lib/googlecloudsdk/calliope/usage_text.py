# Copyright 2013 Google Inc. All Rights Reserved.

"""Generate usage text for displaying to the user.
"""

import argparse
import StringIO
import sys
import textwrap

from googlecloudsdk.core import log

LINE_WIDTH = 80
HELP_INDENT = 25


class _CommandChoiceSuggester(object):
  """Utility to suggest mistyped commands.

  """
  TEST_QUOTA = 5000
  MAX_DISTANCE = 5

  def __init__(self):
    self.cache = {}
    self.inf = float('inf')
    self._quota = self.TEST_QUOTA

  def Deletions(self, s):
    return [s[:i] + s[i + 1:] for i in range(len(s))]

  def GetDistance(self, longer, shorter):
    """Get the edit distance between two words.

    They must be in the correct order, since deletions and mutations only happen
    from 'longer'.

    Args:
      longer: str, The longer of the two words.
      shorter: str, The shorter of the two words.

    Returns:
      int, The number of substitutions or deletions on longer required to get
      to shorter.
    """

    if longer == shorter:
      return 0

    try:
      return self.cache[(longer, shorter)]
    except KeyError:
      pass

    self.cache[(longer, shorter)] = self.inf
    best_distance = self.inf

    if len(longer) > len(shorter):
      if self._quota < 0:
        return self.inf
      self._quota -= 1
      for m in self.Deletions(longer):
        best_distance = min(best_distance, self.GetDistance(m, shorter) + 1)

    if len(longer) == len(shorter):
      # just count how many letters differ
      best_distance = 0
      for i in range(len(longer)):
        if longer[i] != shorter[i]:
          best_distance += 1

    self.cache[(longer, shorter)] = best_distance
    return best_distance

  def SuggestCommandChoice(self, arg, choices):
    """Find the item that is closest to what was attempted.

    Args:
      arg: str, The argument provided.
      choices: [str], The list of valid arguments.

    Returns:
      str, The closest match.
    """

    min_distance = self.inf
    for choice in choices:
      self._quota = self.TEST_QUOTA
      first, second = arg, choice
      if len(first) < len(second):
        first, second = second, first
      if len(first) - len(second) > self.MAX_DISTANCE:
        # Don't bother if they're too different.
        continue
      d = self.GetDistance(first, second)
      if d < min_distance:
        min_distance = d
        bestchoice = choice
    if min_distance > self.MAX_DISTANCE:
      return None
    return bestchoice


def CheckValueAndSuggest(action, value):
  """Override's argparse.ArgumentParser's ._check_value(action, value) method.

  Args:
    action: argparse.Action, The action being checked against this value.
    value: The command line argument provided that needs to correspond to this
        action.

  Raises:
    argparse.ArgumentError: If the action and value don't work together.
  """
  if action.choices is not None and value not in action.choices:

    choices = sorted([choice for choice in action.choices])
    suggestion = _CommandChoiceSuggester().SuggestCommandChoice(value, choices)
    if suggestion:
      suggest = ' Did you mean %r?' % suggestion
    else:
      suggest = ''
    message = """\
Invalid choice: %r.%s
""" % (value, suggest)
    raise argparse.ArgumentError(action, message)


def PrintParserError(parser):
  """Create an error function that knows about the correct parser.

  Args:
    parser: argparse.ArgumentParser, The parser this method is going to be
        tied to.

  Returns:
    func(str): The new .error(message) method.
  """
  def PrintError(message):
    """Override's argparse.ArgumentParser's .error(message) method.

    Specifically, it avoids reprinting the program name and the string "error:".

    Args:
      message: str, The error message to print.
    """
    # pylint:disable=protected-access, Trying to mimic exactly what happens
    # in the argparse code, except for the desired change.
    parser.print_usage(argparse._sys.stderr)
    log.error('({prog}) {message}'.format(prog=parser.prog, message=message))
    parser.exit(2)
  return PrintError


def PrintShortHelpError(parser, command):
  """Create an error function that prints out the short help first.

  Args:
    parser: argparse.ArgumentParser, The parser this method is going to be
        tied to.
    command: calliope._CommandCommon, The command this method is going to be
        tied to.

  Returns:
    func(str): The new .error(message) method.
  """
  def PrintError(message):
    """Override's argparse.ArgumentParser's .error(message) method.

    Specifically, it avoids reprinting the program name and the string "error:".

    Args:
      message: str, The error message to print.
    """
    # pylint:disable=protected-access
    shorthelp = ShortHelpText(command, command._ai)
    argparse._sys.stderr.write(shorthelp + '\n')
    log.error('({prog}) {message}'.format(prog=parser.prog, message=message))
    parser.exit(2)
  return PrintError


def WrapMessageInNargs(message, nargs):
  if nargs == '+':
    return '{0} [{0} ...]'.format(message)
  elif nargs == '*' or nargs == argparse.REMAINDER:
    return '[{0} ...]'.format(message)
  elif nargs == '?':
    return '[{0}]'.format(message)
  else:
    return message


def PositionalDisplayString(arg):
  """Create the display help string for a positional arg.

  Args:
    arg: argparse.Argument, The argument object to be displayed.

  Returns:
    str, The string representation for printing.
  """
  message = arg.metavar or arg.dest.upper()
  return WrapMessageInNargs(message, arg.nargs)


def FlagDisplayString(arg, brief):
  """Create the display help string for a flag arg.

  Args:
    arg: argparse.Argument, The argument object to be displayed.
    brief: bool, If true, only display one version of a flag that has
        multiple versions, and do not display the default value.

  Returns:
    str, The string representation for printing.
  """
  metavar = arg.metavar or arg.dest.upper()
  if brief:
    long_string = sorted(arg.option_strings)[0]
    if arg.nargs == 0:
      return long_string
    return '{flag} {metavar}'.format(
        flag=long_string,
        metavar=WrapMessageInNargs(metavar, arg.nargs))
  else:
    if arg.nargs == 0:
      return ', '.join(arg.option_strings)
    else:
      display_string = ', '.join(
          ['{flag} {metavar}'.format(
              flag=option_string,
              metavar=WrapMessageInNargs(metavar, arg.nargs))
           for option_string in arg.option_strings])
      if not arg.required and arg.default:
        display_string += '; default="{val}"'.format(val=arg.default)
      return display_string


def _WrapWithPrefix(prefix, message, indent, length, spacing,
                    writer=sys.stdout):
  """Helper function that does two-column writing.

  If the first column is too long, the second column begins on the next line.

  Args:
    prefix: str, Text for the first column.
    message: str, Text for the second column.
    indent: int, Width of the first column.
    length: int, Width of both columns, added together.
    spacing: str, Space to put on the front of prefix.
    writer: file-like, Receiver of the written output.
  """
  def W(s):
    writer.write(s)
  def Wln(s):
    W(s + '\n')

  # Reformat the message to be of rows of the correct width, which is what's
  # left-over from length when you subtract indent. The first line also needs
  # to begin with the indent, but that will be taken care of conditionally.
  message = ('\n%%%ds' % indent % ' ').join(
      textwrap.wrap(message, length - indent))
  if len(prefix) > indent - len(spacing) - 2:
    # If the prefix is too long to fit in the indent width, start the message
    # on a new line after writing the prefix by itself.
    Wln('%s%s' % (spacing, prefix))
    # The message needs to have the first line indented properly.
    W('%%%ds' % indent % ' ')
    Wln(message)
  else:
    # If the prefix fits comfortably within the indent (2 spaces left-over),
    # print it out and start the message after adding enough whitespace to make
    # up the rest of the indent.
    W('%s%s' % (spacing, prefix))
    Wln('%%%ds %%s'
        % (indent - len(prefix) - len(spacing) - 1)
        % (' ', message))


def GenerateUsage(command, argument_interceptor):
  """Generate a usage string for a calliope command or group.

  Args:
    command: calliope._CommandCommon, The command or group object that we're
        generating usage for.
    argument_interceptor: calliope._ArgumentInterceptor, the object that tracks
        all of the flags for this command or group.

  Returns:
    str, The usage string.
  """
  buf = StringIO.StringIO()

  command_path = ' '.join(command.GetPath())
  usage_parts = []

  optional_messages = False

  flag_messages = []

  for arg in argument_interceptor.flag_args:
    if arg.help == argparse.SUPPRESS:
      continue
    if not arg.required:
      optional_messages = True
      continue
    # and add it to the usage
    msg = FlagDisplayString(arg, True)
    flag_messages.append(msg)
  usage_parts.extend(sorted(flag_messages))

  if optional_messages:
    # If there are any optional flags, add a simple message to the usage.
    usage_parts.append('[optional flags]')

  # Explicitly not sorting here - order matters.
  for arg in argument_interceptor.positional_args:
    usage_parts.append(PositionalDisplayString(arg))

  group_helps = command.GetSubGroupHelps()
  command_helps = command.GetSubCommandHelps()

  groups = sorted([name for (name, helpmsg)
                   in group_helps.iteritems()
                   if helpmsg != argparse.SUPPRESS])
  commands = sorted([name for (name, helpmsg)
                     in command_helps.iteritems()
                     if helpmsg != argparse.SUPPRESS])

  all_subtypes = []
  if groups:
    all_subtypes.append('group')
  if commands:
    all_subtypes.append('command')
  if groups or commands:
    usage_parts.append('<%s>' % ' | '.join(all_subtypes))

  usage_msg = ' '.join(usage_parts)

  non_option = '{command} '.format(command=command_path)

  buf.write(non_option + usage_msg + '\n')

  if groups:
    _WrapWithPrefix('group may be', ' | '.join(
        groups), HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)
  if commands:
    _WrapWithPrefix('command may be', ' | '.join(
        commands), HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)
  return buf.getvalue()


def ShortHelpText(command, argument_interceptor):
  """Get a command's short help text.

  Args:
    command: calliope._CommandCommon, The command object that we're helping.
    argument_interceptor: calliope._ArgumentInterceptor, the object that tracks
        all of the flags for this command or group.

  Returns:
    str, The short help text.
  """

  buf = StringIO.StringIO()

  required_messages = []
  optional_messages = []

  # Sorting for consistency and readability.
  for arg in argument_interceptor.flag_args:
    if arg.help == argparse.SUPPRESS:
      continue
    message = (FlagDisplayString(arg, False), arg.help or '')
    if not arg.required:
      optional_messages.append(message)
      continue
    required_messages.append(message)
    # and add it to the usage
    msg = FlagDisplayString(arg, True)

  positional_messages = []

  # Explicitly not sorting here - order matters.
  for arg in argument_interceptor.positional_args:
    positional_messages.append(
        (PositionalDisplayString(arg), arg.help or ''))

  group_helps = command.GetSubGroupHelps()
  command_helps = command.GetSubCommandHelps()

  group_messages = [(name, helpmsg)
                    for (name, helpmsg)
                    in group_helps.iteritems()
                    if helpmsg != argparse.SUPPRESS]
  command_messages = [(name, helpmsg)
                      for (name, helpmsg)
                      in command_helps.iteritems()
                      if helpmsg != argparse.SUPPRESS]

  buf.write('Usage: ' + GenerateUsage(command, argument_interceptor) + '\n')

  # Second, print out the long help.

  buf.write('\n'.join(textwrap.wrap(command.long_help or '', LINE_WIDTH)))
  buf.write('\n\n')

  # Third, print out the short help for everything that can come on
  # the command line, grouped into required flags, optional flags,
  # sub groups, sub commands, and positional arguments.

  # This printing is done by collecting a list of rows. If the row is just
  # a string, that means print it without decoration. If the row is a tuple,
  # use _WrapWithPrefix to print that tuple in aligned columns.

  required_flag_msgs = []
  unrequired_flag_msgs = []
  for arg in argument_interceptor.flag_args:
    if arg.help == argparse.SUPPRESS:
      continue
    usage = FlagDisplayString(arg, False)
    msg = (usage, arg.help or '')
    if not arg.required:
      unrequired_flag_msgs.append(msg)
    else:
      required_flag_msgs.append(msg)

  def TextIfExists(title, messages):
    if not messages:
      return None
    textbuf = StringIO.StringIO()
    textbuf.write('%s\n' % title)
    for (arg, helptxt) in messages:
      _WrapWithPrefix(arg, helptxt, HELP_INDENT, LINE_WIDTH,
                      spacing='  ', writer=textbuf)
    return textbuf.getvalue()

  all_messages = [
      TextIfExists('required flags:', sorted(required_messages)),
      TextIfExists('optional flags:', sorted(optional_messages)),
      TextIfExists('positional arguments:', positional_messages),
      TextIfExists('command groups:', sorted(group_messages)),
      TextIfExists('commands:', sorted(command_messages)),
  ]
  buf.write('\n'.join([msg for msg in all_messages if msg]))

  return buf.getvalue()


def ExtractHelpStrings(docstring):
  """Extracts short help and long help from a docstring.

  If the docstring contains a blank line (i.e., a line consisting of zero or
  more spaces), everything before the first blank line is taken as the short
  help string and everything after it is taken as the long help string. The
  short help is flowing text with no line breaks, while the long help may
  consist of multiple lines, each line beginning with an amount of whitespace
  determined by dedenting the docstring.

  If the docstring does not contain a blank line, the sequence of words in the
  docstring is used as both the short help and the long help.

  Corner cases: If the first line of the docstring is empty, everything
  following it forms the long help, and the sequence of words of in the long
  help (without line breaks) is used as the short help. If the short help
  consists of zero or more spaces, None is used instead. If the long help
  consists of zero or more spaces, the short help (which might or might not be
  None) is used instead.

  Args:
    docstring: The docstring from which short and long help are to be taken

  Returns:
    a tuple consisting of a short help string and a long help string

  """
  if docstring:
    unstripped_doc_lines = docstring.splitlines()
    stripped_doc_lines = [s.strip() for s in unstripped_doc_lines]
    try:
      empty_line_index = stripped_doc_lines.index('')
      short_help = ' '.join(stripped_doc_lines[:empty_line_index])
      raw_long_help = '\n'.join(unstripped_doc_lines[empty_line_index + 1:])
      long_help = textwrap.dedent(raw_long_help).strip()
    except ValueError:  # no empty line in stripped_doc_lines
      short_help = ' '.join(stripped_doc_lines).strip()
      long_help = None
    if not short_help:  # docstring started with a blank line
      short_help = ' '.join(stripped_doc_lines[empty_line_index + 1:]).strip()
      # words of long help as flowing text
    return (short_help or None, long_help or short_help or None)
  else:
    return (None, None)
