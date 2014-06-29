# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing backend services."""
from googlecloudsdk.compute.lib import base_classes


class List(base_classes.GlobalLister):
  """List backend services."""

  @property
  def service(self):
    return self.context['compute'].backendServices

  @property
  def print_resource_type(self):
    return 'backendServices'


List.detailed_help = {
    'brief': 'List backend services',
    'DESCRIPTION': """\
        *{command}* lists summary information of backend services in a
        project. The ``--uri'' option can be used to display URIs for
        the backend services.
        """,
}
