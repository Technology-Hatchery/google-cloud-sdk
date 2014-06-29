# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting disks."""
from googlecloudsdk.compute.lib import base_classes


class GetDisks(base_classes.ZonalGetter):
  """Get Google Compute Engine disks."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'disks')

  @property
  def service(self):
    return self.context['compute'].disks

  @property
  def print_resource_type(self):
    return 'disks'


GetDisks.detailed_help = {
    'brief': 'Get Google Compute Engine disks',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine disks in a project.

        By default, disks from all zones are fetched. The results can
        be narrowed down by providing ``--zone''.
        """,
}
