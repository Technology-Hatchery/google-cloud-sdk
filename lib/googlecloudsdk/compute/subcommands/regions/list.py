# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing regions."""
from googlecloudsdk.compute.lib import base_classes


class ListRegions(base_classes.GlobalLister):
  """List Google Compute Engine regions."""

  @property
  def service(self):
    return self.context['compute'].regions

  @property
  def print_resource_type(self):
    return 'regions'
