# Copyright 2013 Google Inc. All Rights Reserved.

"""'dns managed-zone list' command."""

from apiclient import errors

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.dns import util


class List(base.Command):
  """List Cloud DNS managed zones."""
  DEFAULT_MAX_RESULTS = 0
  DEFAULT_PAGE_SIZE = 1000

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--max_results', required=False, help='If greater than zero, limit the '
        'number of changes returned to <max_results>.  '
        'Default: %d' % List.DEFAULT_MAX_RESULTS)

  def Run(self, args):
    """Run 'dns managed-zone list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A list of dict objects representing the zone resource obtained by the
      list operation if the list was successful.
    """
    dns = self.context['dns']
    project = properties.VALUES.core.project.Get(required=True)

    max_results = List.DEFAULT_MAX_RESULTS
    if args.max_results is not None:
      max_results = int(args.max_results)

    if max_results > 0:
      page_size = min(max_results, List.DEFAULT_PAGE_SIZE)
    else:
      page_size = List.DEFAULT_PAGE_SIZE

    request = dns.managedZones().list(project=project, maxResults=page_size)

    try:
      result_list = []
      result = request.execute()
      result_list.extend(result['managedZones'])
      while ((max_results <= 0 or len(result_list) < max_results) and
             'nextPageToken' in result and result['nextPageToken'] is not None):
        if max_results > 0:
          page_size = min(
              max_results - len(result_list), List.DEFAULT_PAGE_SIZE)
        request = dns.managedZones().list(project=project,
                                          maxResults=page_size,
                                          pageToken=result['nextPageToken'])
        result = request.execute()
        result_list.extend(result['managedZones'])
      return result_list
    except errors.HttpError as error:
      raise exceptions.HttpException(util.GetError(error, verbose=True))
    except errors.Error as error:
      raise exceptions.ToolException(error)

  def Display(self, unused_args, result):
    """Display prints information about what just happened to stdout.

    Args:
      unused_args: The same as the args in Run.
      result: The results of the Run() method.
    """
    util.PrettyPrint(result)
