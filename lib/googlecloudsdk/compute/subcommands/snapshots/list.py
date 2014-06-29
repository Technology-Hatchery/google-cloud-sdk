# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing snapshots."""
from googlecloudsdk.compute.lib import base_classes


class ListSnapshots(base_classes.GlobalLister):
  """List Google Compute Engine snapshots."""

  @property
  def service(self):
    return self.context['compute'].snapshots

  @property
  def print_resource_type(self):
    return 'snapshots'
