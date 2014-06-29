# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for adding instances to target pools."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class AddInstances(base_classes.BaseAsyncMutator):
  """Add instances to a target pool."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--instances',
        help='Specifies a list of instances to add to the target pool.',
        metavar='INSTANCE',
        nargs='+',
        required=True)

    parser.add_argument(
        '--region',
        help='The region of the target pool.',
        required=True)

    parser.add_argument(
        '--zone',
        help='The zone of the instances.',
        required=True)

    parser.add_argument(
        'name',
        help='The name of the target pool to which to add the instances.')

  @property
  def service(self):
    return self.context['compute'].targetPools

  @property
  def method(self):
    return 'AddInstance'

  @property
  def print_resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    instances = [messages.InstanceReference(
        instance=self.context['uri-builder'].Build(
            'zones', args.zone, 'instances', instance))
                 for instance in args.instances]

    request = messages.ComputeTargetPoolsAddInstanceRequest(
        region=args.region,
        project=self.context['project'],
        targetPool=args.name,
        targetPoolsAddInstanceRequest=messages.TargetPoolsAddInstanceRequest(
            instances=instances))
    return [request]


AddInstances.detailed_help = {
    'brief': 'Add instances to a target pool',
    'DESCRIPTION': """\
        *{command}* is used to add one or more instances to a target pool.
        For more information on health checks and load balancing, see
        link:https://developers.google.com/compute/docs/load-balancing/[].
        """,
}
