# Copyright 2013 Google Inc. All Rights Reserved.

"""Lists customizable MySQL flags for Google Cloud SQL instances."""
from apiclient import errors

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.sql import util


class List(base.Command):
  """Lists customizable MySQL flags for Google Cloud SQL instances."""

  def Run(self, unused_args):
    """Lists customizable MySQL flags for Google Cloud SQL instances.

    Args:
      unused_args: argparse.Namespace, The arguments that this command was
          invoked with.

    Returns:
      A dict object that has the list of flag resources if the command ran
      successfully.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql = self.context['sql']
    request = sql.flags().list()
    try:
      result = request.execute()
      return result
    except errors.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))
    except errors.Error as error:
      raise exceptions.ToolException(error)

  def Display(self, unused_args, result):
    """Display prints information about what just happened to stdout.

    Args:
      unused_args: The same as the args in Run.
      result: the value returned by Run().
    """
    PrettyPrintFlagsList(result)


def PrettyPrintFlagsList(flags_list):
  """Pretty prints a list of flags.

  Args:
    flags_list: A dict object representing the the list of flag resources.
  """
  printer = util.PrettyPrinter(0)
  for flag in sorted(flags_list['items'], key=lambda flag: flag['name']):
    printer.Print('%s' % flag['name'])
    printer.indent += util.EXTRA_INDENT
    PrettyPrintFlag(flag, printer)
    printer.indent -= util.EXTRA_INDENT
    printer.Print('')


def PrettyPrintFlag(flag, printer):
  """Pretty prints a flag resource.

  Args:
    flag: A dict object representing the flag resource.
    printer: A pretty printer object.
  """
  # Manually express these as the alphabetical ordering of the print doesn't
  # make any sense
  printer.Print('type: %s' % (flag['type'],))
  printer.PrintList('appliesTo', flag['appliesTo'])

  for key in ['minValue', 'maxValue']:
    if key in flag:
      printer.Print('%s: %s' % (key, flag[key]))

  if 'allowedStringValues' in flag:
    printer.PrintList('allowedStringValues', flag['allowedStringValues'])
