# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing images."""
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import image_utils


class ListImages(image_utils.ImageResourceFetcher,
                 base_classes.GlobalLister):
  """List Google Compute Engine images."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalLister.Args(parser)
    image_utils.AddImageFetchingArgs(parser)

  @property
  def service(self):
    return self.context['compute'].images

  @property
  def print_resource_type(self):
    return 'images'
