# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting operations."""
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import operations_utils


class GetOperations(operations_utils.OperationsResourceFetcherMixin,
                    base_classes.BaseGetter):
  """Get Google Compute Engine operations."""

  @staticmethod
  def Args(parser):
    base_classes.BaseGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'operations')
    operations_utils.AddOperationFetchingArgs(parser)

  @property
  def print_resource_type(self):
    return 'operations'


GetOperations.detailed_help = {
    'brief': 'Get Google Compute Engine operations',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine operations in a project.

        By default, global operations and operations from all regions and
        zones are fetched. The results can be narrowed down by providing
        ``--global'', ``--regions'' and/or ``--zones''.
        """,
}
