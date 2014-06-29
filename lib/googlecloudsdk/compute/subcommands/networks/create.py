# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating networks."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class CreateNetwork(base_classes.BaseAsyncMutator):
  """Create Google Compute Engine networks."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional, textual description for the network.')

    range_arg = parser.add_argument(
        '--range',
        help='Specifies the IPv4 address range of this network.',
        default='10.0.0.0/8')
    range_arg.detailed_help = """\
        Specifies the IPv4 address range of this network. The range
        must be specified in CIDR format:
        link:http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing[]. If
        omitted, 10.0.0.0/8 is used.
        """

    parser.add_argument(
        'name',
        help='The name of the network.')

  @property
  def service(self):
    return self.context['compute'].networks

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'networks'

  def CreateRequests(self, args):
    """Returns the request necessary for adding the network."""
    request = messages.ComputeNetworksInsertRequest(
        network=messages.Network(
            name=args.name,
            IPv4Range=args.range,
            description=args.description),
        project=self.context['project'])

    return [request]


CreateNetwork.detailed_help = {
    'brief': 'Create a Google Compute Engine network',
    'DESCRIPTION': """\
        *{command}* is used to create virtual networks. A network
        performs the same function that a router does in a home
        network: it describes the network range and gateway IP
        address, handles communication between instances, and serves
        as a gateway between instances and callers outside the
        network.
        """,
}
