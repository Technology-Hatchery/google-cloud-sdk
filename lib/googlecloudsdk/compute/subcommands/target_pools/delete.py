# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting target pools."""
from googlecloudsdk.compute.lib import base_classes


class DeleteTargetPools(base_classes.RegionalDeleter):
  """Delete target pools."""

  @property
  def service(self):
    return self.context['compute'].targetPools

  @property
  def collection(self):
    return 'targetPools'


DeleteTargetPools.detailed_help = {
    'brief': 'Delete target pools',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine target pools.
        """,
}
