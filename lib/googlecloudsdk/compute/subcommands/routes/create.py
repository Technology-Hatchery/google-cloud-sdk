# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating routes."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import base_classes


class Create(base_classes.BaseAsyncMutator):
  """Create a new route."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional, textual description for the route.')

    parser.add_argument(
        '--network',
        default='default',
        help='Specifies the network to which the route will be applied.')

    tags = parser.add_argument(
        '--tags',
        default=[],
        metavar='TAG',
        nargs='+',
        help='Identifies the set of instances that this route will apply to.')
    tags.detailed_help = """\
        Identifies the set of instances that this route will apply to. If no
        tags are provided, the route will apply to all instances in the network.
        """

    destination_range = parser.add_argument(
        '--destination-range',
        required=True,
        help=('The destination range of outgoing packets that the route will '
              'apply to.'))
    destination_range.detailed_help = """\
        The destination range of outgoing packets that the route will
        apply to. To match all traffic, use ``0.0.0.0/0''.
        """

    priority = parser.add_argument(
        '--priority',
        default=1000,
        help=('Specifies the priority of this route relative to other routes '
              'with the same specifity.'),
        type=int)
    priority.detailed_help = """\
        Specifies the priority of this route relative to other routes
        with the same specifity. The lower the value, the higher the
        priority.
        """

    next_hop = parser.add_mutually_exclusive_group(required=True)

    next_hop_instance = next_hop.add_argument(
        '--next-hop-instance',
        help=('Specifies the name of an instance that should handle traffic '
              'matching this route.'))
    next_hop_instance.detailed_help = """\
        Specifies the name of an instance that should handle traffic
        matching this route. When this flag is specified, the zone of
        the instance must be specified using
        ``--next-hop-instance-zone''.
        """

    parser.add_argument(
        '--next-hop-instance-zone',
        help='The zone of the next hop instance.')

    next_hop_address = next_hop.add_argument(
        '--next-hop-address',
        help=('Specifies the IP address of an instance that should handle '
              'matching packets.'))
    next_hop_address.detailed_help = """\
        Specifies the IP address of an instance that should handle
        matching packets. The instance must have IP forwarding enabled
        (i.e., include ``--can-ip-forward'' when creating the instance
        using 'gcloud compute instances create')
        """

    next_hop_gateway = next_hop.add_argument(
        '--next-hop-gateway',
        help='Specifies the gateway that should handle matching packets.')
    next_hop_gateway.detailed_help = """\
        Specifies the gateway that should handle matching
        packets. Currently, the only acceptable value is
        ``default-internet-gateway'' which is a gateway operated by
        Google Compute Engine.
        """

    parser.add_argument(
        'name',
        help='The name to assign to the route.')

  @property
  def service(self):
    return self.context['compute'].routes

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return None

  def CreateRequests(self, args):
    network_uri = self.context['uri-builder'].Build(
        'global', 'networks', args.network)

    if args.next_hop_instance:
      if not args.next_hop_instance_zone:
        raise exceptions.ToolException(
            'when specifying a next hop instance, the zone of the instance '
            'must be specified using --next-hop-instance-zone')

      next_hop_instance_uri = self.context['uri-builder'].Build(
          'zones', args.next_hop_instance_zone,
          'instances', args.next_hop_instance)
    else:
      if args.next_hop_instance_zone:
        raise exceptions.ToolException(
            '--next-hop-instance-zone can only be specified in conjunction '
            'with --next-hop-instance')
      next_hop_instance_uri = None

    if args.next_hop_gateway:
      next_hop_gateway_uri = self.context['uri-builder'].Build(
          'global', 'gateways', args.next_hop_gateway)
    else:
      next_hop_gateway_uri = None

    request = messages.ComputeRoutesInsertRequest(
        project=self.context['project'],
        route=messages.Route(
            description=args.description,
            destRange=args.destination_range,
            name=args.name,
            network=network_uri,
            nextHopInstance=next_hop_instance_uri,
            nextHopIp=args.next_hop_address,
            nextHopGateway=next_hop_gateway_uri,
            priority=args.priority,
            tags=args.tags,
        ))
    return [request]


Create.detailed_help = {
    'brief': 'Create a new route',
    'DESCRIPTION': """\
        *{command}* is used to create routes. A route is a rule that
         specifies how certain packets should be handled by the
         virtual network. Routes are associated with virtual machine
         instances by tag, and the set of routes for a particular VM
         is called its routing table. For each packet leaving a
         virtual machine, the system searches that machine's routing
         table for a single best matching route.

        Routes match packets by destination IP address, preferring
        smaller or more specific ranges over larger ones (see
        ``--destination-range''). If there is a tie, the system selects
        the route with the smallest priority value. If there is still
        a tie, it uses the layer three and four packet headers to
        select just one of the remaining matching routes. The packet
        is then forwarded as specified by ``--next-hop-address'',
        ``--next-hop-instance'', or ``--next-hop-gateway'' of the
        winning route. Packets that do not match any route in the
        sending virtual machine routing table will be dropped.
        """,
}
