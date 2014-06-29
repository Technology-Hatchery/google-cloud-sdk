# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for resetting an instance."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class Reset(base_classes.BaseAsyncMutator):
  """Reset a virtual machine instance."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--zone',
        help='Specifies the zone of the instance.',
        required=True)
    parser.add_argument(
        'name',
        help='The name of the instance to reset.')

  @property
  def service(self):
    return self.context['compute'].instances

  @property
  def method(self):
    return 'Reset'

  @property
  def print_resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    request = messages.ComputeInstancesResetRequest(
        instance=args.name,
        project=self.context['project'],
        zone=args.zone)
    return [request]


Reset.detailed_help = {
    'brief': 'Reset a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is used to perform a hard reset on a Google
        Compute Engine virtual machine.
        """,
}
