# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting addresses."""
from googlecloudsdk.compute.lib import base_classes


class Release(base_classes.RegionalDeleter):
  """Release reserved IP addresses."""

  @property
  def service(self):
    return self.context['compute'].addresses

  @property
  def collection(self):
    return 'addresses'


Release.detailed_help = {
    'brief': 'Release reserved IP addresses',
    'DESCRIPTION': """\
        *{command}* releases one or more Google Compute Engine IP
         addresses.
        """,
}
