# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting backend services."""
from googlecloudsdk.compute.lib import base_classes


class Delete(base_classes.GlobalDeleter):
  """Delete backend services."""

  @property
  def service(self):
    return self.context['compute'].backendServices

  @property
  def collection(self):
    return 'backendServices'


Delete.detailed_help = {
    'brief': 'Delete backend services',
    'DESCRIPTION': """\
        *{command}* deletes one or more backend services.
        """,
}
