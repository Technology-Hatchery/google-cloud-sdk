# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting networks."""
from googlecloudsdk.compute.lib import base_classes


class DeleteNetworks(base_classes.GlobalDeleter):
  """Delete Google Compute Engine networks."""

  @property
  def service(self):
    return self.context['compute'].networks

  @property
  def collection(self):
    return 'networks'


DeleteNetworks.detailed_help = {
    'brief': 'Delete Google Compute Engine networks',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine
        networks. Networks can only be deleted when no other resources
        (e.g., virtual machine instances) refer to them.
        """,
}
