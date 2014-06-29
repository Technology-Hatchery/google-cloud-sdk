# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating target instances."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class Create(base_classes.BaseAsyncMutator):
  """Create a target instance for handling traffic from a forwarding rule."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional, textual description of the target instance.')
    parser.add_argument(
        '--instance',
        required=True,
        help=('The name of the virtual machine instance that will handle the '
              'traffic.'))

    parser.add_argument(
        '--zone',
        help=('The zone of the target instance (i.e., where the instance '
              'resides).'),
        required=True)

    parser.add_argument(
        'name',
        help='The name of the target instance.')

  @property
  def service(self):
    return self.context['compute'].targetInstances

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'targetInstances'

  def CreateRequests(self, args):
    instance_uri = self.context['uri-builder'].Build(
        'zones', args.zone, 'instances', args.instance)

    request = messages.ComputeTargetInstancesInsertRequest(
        targetInstance=messages.TargetInstance(
            description=args.description,
            name=args.name,
            instance=instance_uri,
        ),
        project=self.context['project'],
        zone=args.zone)

    return [request]


Create.detailed_help = {
    'brief': (
        'Create a target instance for handling traffic from a forwarding rule'),
    'DESCRIPTION': """\
        *{command}* is used to create a target instance for handling
        traffic from one or more forwarding rules. Target instances
        are ideal for traffic that should be managed by a single
        source. For more information on target instances, see
        link:https://developers.google.com/compute/docs/protocol-forwarding/#targetinstances[].
        """,
}
