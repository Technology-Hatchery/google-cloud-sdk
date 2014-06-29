# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting firewalls."""
from googlecloudsdk.compute.lib import base_classes


class DeleteFirewalls(base_classes.GlobalDeleter):
  """Delete Google Compute Engine firewall rules."""

  @property
  def service(self):
    return self.context['compute'].firewalls

  @property
  def collection(self):
    return 'firewalls'


DeleteFirewalls.detailed_help = {
    'brief': 'Delete Google Compute Engine firewall rules',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine firewall
         rules.
        """,
}
