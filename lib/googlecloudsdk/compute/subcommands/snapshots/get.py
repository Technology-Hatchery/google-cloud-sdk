# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting snapshots."""
from googlecloudsdk.compute.lib import base_classes


class GetSnapshots(base_classes.GlobalGetter):
  """Get Google Compute Engine snapshots."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'snapshots')

  @property
  def service(self):
    return self.context['compute'].snapshots

  @property
  def print_resource_type(self):
    return 'snapshots'


GetSnapshots.detailed_help = {
    'brief': 'Get Google Compute Engine snapshots',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine snapshots in a project.
        """,
}
