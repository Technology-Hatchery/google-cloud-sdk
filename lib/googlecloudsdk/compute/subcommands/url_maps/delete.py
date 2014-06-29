# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting URL maps."""
from googlecloudsdk.compute.lib import base_classes


class Delete(base_classes.GlobalDeleter):
  """Delete backend services."""

  @property
  def service(self):
    return self.context['compute'].urlMaps

  @property
  def collection(self):
    return 'urlMaps'


Delete.detailed_help = {
    'brief': 'Delete URL maps',
    'DESCRIPTION': """\
        *{command}* deletes one or more URL maps.
        """,
}
