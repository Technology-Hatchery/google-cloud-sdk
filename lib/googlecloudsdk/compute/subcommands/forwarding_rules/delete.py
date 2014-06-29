# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for deleting forwarding rules."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import forwarding_rules_utils as utils


class DeleteForwardingRule(utils.ForwardingRulesMutator):
  """Delete forwarding rules."""

  @staticmethod
  def Args(parser):
    utils.ForwardingRulesMutator.Args(parser)

    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        help='The names of the forwarding rules to delete.')

  @property
  def method(self):
    return 'Delete'

  def CreateGlobalRequests(self, args):
    """Create a globally scoped request."""

    requests = []
    for name in args.names:
      request = messages.ComputeGlobalForwardingRulesDeleteRequest(
          forwardingRule=name,
          project=self.context['project'],
      )
      requests.append(request)

    return requests

  def CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""

    requests = []
    for name in args.names:
      request = messages.ComputeForwardingRulesDeleteRequest(
          forwardingRule=name,
          project=self.context['project'],
          region=args.region,
      )
      requests.append(request)

    return requests


DeleteForwardingRule.detailed_help = {
    'brief': 'Delete forwarding rules',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine forwarding rules.
        """,
}
