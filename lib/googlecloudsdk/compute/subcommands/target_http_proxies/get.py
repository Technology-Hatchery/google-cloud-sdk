# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting target HTTP proxies."""
from googlecloudsdk.compute.lib import base_classes


class Get(base_classes.GlobalGetter):
  """Display detailed information about target HTTP proxies."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'targetHttpProxies')

  @property
  def service(self):
    return self.context['compute'].targetHttpProxies

  @property
  def print_resource_type(self):
    return 'targetHttpProxies'


Get.detailed_help = {
    'brief': 'Display detailed information about target HTTP proxies',
    'DESCRIPTION': """\
        *{command}* displays all data associated with target HTTP proxies
        in a project.
        """,
}
