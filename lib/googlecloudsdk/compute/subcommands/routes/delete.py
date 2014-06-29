# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting routes."""
from googlecloudsdk.compute.lib import base_classes


class Delete(base_classes.GlobalDeleter):
  """Delete routes."""

  @property
  def service(self):
    return self.context['compute'].routes

  @property
  def collection(self):
    return 'routes'


Delete.detailed_help = {
    'brief': 'Delete routes',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine routes.
        """,
}
