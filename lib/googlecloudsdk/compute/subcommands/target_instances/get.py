# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting target instances."""
from googlecloudsdk.compute.lib import base_classes


class Get(base_classes.ZonalGetter):
  """Get target instances."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'targetInstances')

  @property
  def service(self):
    return self.context['compute'].targetInstances

  @property
  def print_resource_type(self):
    return 'targetInstances'


Get.detailed_help = {
    'brief': 'Get target instances',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine target instances in a project.

        By default, target instances from all zones are fetched. The
        results can be narrowed down by providing ``--zone''.
        """,
}
