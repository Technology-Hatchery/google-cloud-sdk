# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating firewalls."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import firewalls_utils


class CreateFirewall(base_classes.BaseAsyncMutator):
  """Create Google Compute Engine firewalls."""

  @staticmethod
  def Args(parser):
    allow = parser.add_argument(
        '--allow',
        nargs='+',
        metavar=firewalls_utils.ALLOWED_METAVAR,
        help='The list of IP protocols and ports which will be allowed.',
        required=True)
    allow.detailed_help = """\
        A list of protocols and ports whose traffic will be allowed.
        +
        'PROTOCOL' is the IP protocol whose traffic will be allowed.
        'PROTOCOL' can be either the name of a well-known protocol
        (e.g., ``tcp'' or ``icmp'') or the IP protocol number.
        A list of IP protocols can be found at
        link:http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml[].
        +
        A port or port range can be specified after 'PROTOCOL' to
        allow traffic through specific ports. If no port or port range
        is specified, connections through all ranges are allowed. For
        example, the following will create a rule that allows TCP traffic
        through port 80 and allows ICMP traffic:

          $ {command} my-rule --allow tcp:80 icmp
        +
        TCP and UDP rules must include a port or port range.
        """

    parser.add_argument(
        '--description',
        help='An optional, textual description for the firewall.')

    network = parser.add_argument(
        '--network',
        default='default',
        help='The network to which this rule is attached.')
    network.detailed_help = """\
        The network to which this rule is attached. If omitted, the
        rule is attached to the ``default'' network.
        """

    source_ranges = parser.add_argument(
        '--source-ranges',
        default=[],
        metavar='CIDR_RANGE',
        nargs='+',
        help=('A list of IP address blocks that may make inbound connections '
              'in CIDR format.'))
    source_ranges.detailed_help = """\
        A list of IP address blocks that are allowed to make inbound
        connections that match the firewall rule to the instances on
        the network. The IP address blocks must be specified in CIDR
        format:
        link:http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing[].
        If neither --source-ranges nor --source-tags is provided, then this
        flag will default to ``0.0.0.0/0'', allowing all sources.
        """

    source_tags = parser.add_argument(
        '--source-tags',
        default=[],
        metavar='TAG',
        nargs='+',
        help=('A list of instance tags indicating the set of instances on the '
              'network which may accept inbound connections that match the '
              'firewall rule.'))
    source_tags.detailed_help = """\
        A list of instance tags indicating the set of instances on the
        network which may accept inbound connections that match the
        firewall rule. If omitted, all instances on the network can
        receive inbound connections that match the rule.
        +
        Tags can be assigned to instances during instance creation.
        """

    target_tags = parser.add_argument(
        '--target-tags',
        default=[],
        metavar='TAG',
        nargs='+',
        help=('A list of instance tags indicating the set of instances on the '
              'network which may make network connections that match the '
              'firewall rule.'))
    target_tags.detailed_help = """\
        A list of instance tags indicating the set of instances on the
        network which may make network connections that match the
        firewall rule. If omitted, all instances on the network can
        make connections that match the rule.
        +
        Tags can be assigned to instances during instance creation.
        """

    parser.add_argument(
        'name',
        help='The name of the firewall to create.')

  @property
  def service(self):
    return self.context['compute'].firewalls

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'firewalls'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding firewalls."""
    if not args.source_ranges and not args.source_tags:
      args.source_ranges = ['0.0.0.0/0']

    allowed = firewalls_utils.ParseAllowed(args.allow)

    network_uri = self.context['uri-builder'].Build(
        'global', 'networks', args.network)

    request = messages.ComputeFirewallsInsertRequest(
        firewall=messages.Firewall(
            allowed=allowed,
            name=args.name,
            description=args.description,
            network=network_uri,
            sourceRanges=args.source_ranges,
            sourceTags=args.source_tags,
            targetTags=args.target_tags),
        project=self.context['project'])
    return [request]


CreateFirewall.detailed_help = {
    'brief': 'Create a Google Compute Engine firewall rule',
    'DESCRIPTION': """\
        *{command}* is used to create firewall rules to allow incoming
        traffic to a network.
        """,
}
