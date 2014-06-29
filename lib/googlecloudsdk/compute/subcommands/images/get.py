# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting images."""
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import image_utils


class GetImages(image_utils.ImageResourceFetcher,
                base_classes.GlobalGetter):
  """Get Google Compute Engine images."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    image_utils.AddImageFetchingArgs(parser)
    base_classes.AddFieldsFlag(parser, 'images')

  @property
  def service(self):
    return self.context['compute'].images

  @property
  def print_resource_type(self):
    return 'images'


GetImages.detailed_help = {
    'brief': 'Get Google Compute Engine images',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine images in a project.
        """,
}
