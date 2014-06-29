# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing persistent disks."""
from googlecloudsdk.compute.lib import base_classes


class ListDisks(base_classes.ZonalLister):
  """List Google Compute Engine persistent disks."""

  @property
  def service(self):
    return self.context['compute'].disks

  @property
  def print_resource_type(self):
    return 'disks'
