# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting regions."""
from googlecloudsdk.compute.lib import base_classes


class GetRegions(base_classes.GlobalGetter):
  """Get Google Compute Engine regions."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'regions')

  @property
  def service(self):
    return self.context['compute'].regions

  @property
  def print_resource_type(self):
    return 'regions'


GetRegions.detailed_help = {
    'brief': 'Get Google Compute Engine regions',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine regions.
        """,
}
