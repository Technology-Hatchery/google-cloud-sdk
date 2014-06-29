# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting snapshots."""
from googlecloudsdk.compute.lib import base_classes


class DeleteSnapshots(base_classes.GlobalDeleter):
  """Delete Google Compute Engine snapshots."""

  @property
  def service(self):
    return self.context['compute'].snapshots

  @property
  def collection(self):
    return 'snapshots'


DeleteSnapshots.detailed_help = {
    'brief': 'Delete Google Compute Engine snapshots',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine
         snapshots.
        """,
}
