# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting routes."""
from googlecloudsdk.compute.lib import base_classes


class Get(base_classes.GlobalGetter):
  """Get routes."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'routes')

  @property
  def service(self):
    return self.context['compute'].routes

  @property
  def print_resource_type(self):
    return 'routes'


Get.detailed_help = {
    'brief': 'Get routes',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine routes in a project.
        """,
}
