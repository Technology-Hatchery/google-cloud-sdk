# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting backend services."""
from googlecloudsdk.compute.lib import base_classes


class Get(base_classes.GlobalGetter):
  """Get backend services."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'backendServices')

  @property
  def service(self):
    return self.context['compute'].backendServices

  @property
  def print_resource_type(self):
    return 'backendServices'


Get.detailed_help = {
    'brief': 'Get backend services',
    'DESCRIPTION': """\
        *{command}* displays all data associated with backend services in a
        project.
        """,
}
