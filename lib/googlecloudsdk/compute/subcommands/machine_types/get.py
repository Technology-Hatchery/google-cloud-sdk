# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting machine types."""
from googlecloudsdk.compute.lib import base_classes


class GetMachineTypes(base_classes.ZonalGetter):
  """Get Google Compute Engine machine types."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'machineTypes')

  @property
  def service(self):
    return self.context['compute'].machineTypes

  @property
  def print_resource_type(self):
    return 'machineTypes'


GetMachineTypes.detailed_help = {
    'brief': 'Get Google Compute Engine machine types',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine machine types in a project.

        By default, machine types from all zones are fetched. The results can
        be narrowed down by providing ``--zone''.
        """,
}
