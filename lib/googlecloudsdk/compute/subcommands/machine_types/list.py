# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing machine types."""
from googlecloudsdk.compute.lib import base_classes


class ListMachineTypes(base_classes.ZonalLister):
  """List Google Compute Engine machine types."""

  @property
  def service(self):
    return self.context['compute'].machineTypes

  @property
  def print_resource_type(self):
    return 'machineTypes'
