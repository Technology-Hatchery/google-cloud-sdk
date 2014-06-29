# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting target pools."""
from googlecloudsdk.compute.lib import base_classes


class GetTargetPools(base_classes.RegionalGetter):
  """Get target pools."""

  @staticmethod
  def Args(parser):
    base_classes.RegionalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'targetPools')

  @property
  def service(self):
    return self.context['compute'].targetPools

  @property
  def print_resource_type(self):
    return 'targetPools'


GetTargetPools.detailed_help = {
    'brief': 'Get Google Compute Engine target pools',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine target pools in a project.

        By default, target pools from all regions are fetched. The results can
        be narrowed down by providing ``--region''.
        """,
}
