# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting networks."""
from googlecloudsdk.compute.lib import base_classes


class DeleteImages(base_classes.GlobalDeleter):
  """Delete Google Compute Engine images."""

  @property
  def service(self):
    return self.context['compute'].images

  @property
  def collection(self):
    return 'images'


DeleteImages.detailed_help = {
    'brief': 'Delete Google Compute Engine images',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine images.
        """,
}
