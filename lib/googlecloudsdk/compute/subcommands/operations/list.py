# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing operations."""
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import operations_utils


class ListOperations(operations_utils.OperationsResourceFetcherMixin,
                     base_classes.BaseLister):
  """List Google Compute Engine operations."""

  @staticmethod
  def Args(parser):
    base_classes.BaseLister.Args(parser)
    operations_utils.AddOperationFetchingArgs(parser)

  @property
  def print_resource_type(self):
    return 'operations'
