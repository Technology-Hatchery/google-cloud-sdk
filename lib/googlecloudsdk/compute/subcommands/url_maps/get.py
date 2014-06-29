# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting url maps."""
from googlecloudsdk.compute.lib import base_classes


class Get(base_classes.GlobalGetter):
  """Get URL maps."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'urlMaps')

  @property
  def service(self):
    return self.context['compute'].urlMaps

  @property
  def print_resource_type(self):
    return 'urlMaps'


Get.detailed_help = {
    'brief': 'Get URL maps',
    'DESCRIPTION': """\
        *{command}* displays all data associated with URL maps in a
        project.
        """,
}
