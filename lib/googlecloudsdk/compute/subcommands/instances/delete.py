# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting instances."""
from googlecloudsdk.compute.lib import base_classes


class DeleteInstances(base_classes.ZonalDeleter):
  """Delete Google Compute Engine virtual machine instances."""

  @property
  def service(self):
    return self.context['compute'].instances

  @property
  def collection(self):
    return 'instances'


DeleteInstances.detailed_help = {
    'brief': 'Delete Google Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine virtual machine
        instances.
        """,
}
