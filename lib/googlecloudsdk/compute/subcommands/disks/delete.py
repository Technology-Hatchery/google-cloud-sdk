# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting disks."""
from googlecloudsdk.compute.lib import base_classes


class DeleteDisks(base_classes.ZonalDeleter):
  """Delete Google Compute Engine disks."""

  @property
  def service(self):
    return self.context['compute'].disks

  @property
  def collection(self):
    return 'disks'


DeleteDisks.detailed_help = {
    'brief': 'Delete Google Compute Engine persistent disks',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine
        persistent disks. Disks can be deleted only if they are not
        being used by any virtual machine instances.
        """,
}
