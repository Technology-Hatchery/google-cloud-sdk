# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting addresses."""
from googlecloudsdk.compute.lib import base_classes


class GetAddresses(base_classes.RegionalGetter):
  """Get Google Compute Engine static addresses."""

  @staticmethod
  def Args(parser):
    base_classes.RegionalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'addresses')

  @property
  def service(self):
    return self.context['compute'].addresses

  @property
  def print_resource_type(self):
    return 'addresses'


GetAddresses.detailed_help = {
    'brief': 'Get Google Compute Engine static addresses',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine static IP addresses in a project.

        By default, addresses from all regions are fetched. The results can
        be narrowed down by providing ``--region''.
        """,
}
