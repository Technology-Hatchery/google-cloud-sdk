# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting firewalls."""
from googlecloudsdk.compute.lib import base_classes


class GetFirewalls(base_classes.GlobalGetter):
  """Get Google Compute Engine firewall rules."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalGetter.Args(parser)
    base_classes.AddFieldsFlag(parser, 'firewalls')

  @property
  def service(self):
    return self.context['compute'].firewalls

  @property
  def print_resource_type(self):
    return 'firewalls'


GetFirewalls.detailed_help = {
    'brief': 'Get Google Compute Engine firewall rules',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine firewall rules in a project.
        """,
}
