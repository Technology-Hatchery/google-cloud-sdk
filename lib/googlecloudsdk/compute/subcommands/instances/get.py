# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting instances."""
from googlecloudsdk.compute.lib import base_classes


class GetInstances(base_classes.ZonalGetter):
  """Get Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'instances')

  @property
  def service(self):
    return self.context['compute'].instances

  @property
  def print_resource_type(self):
    return 'instances'


GetInstances.detailed_help = {
    'brief': 'Get Google Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine virtual machine instances in a project.

        By default, instances from all zones are fetched. The results can
        be narrowed down by providing ``--zone''.
        """,
}
