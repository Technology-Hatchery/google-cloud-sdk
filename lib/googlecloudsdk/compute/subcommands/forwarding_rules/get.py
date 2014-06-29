# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting forwarding rules."""
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import forwarding_rules_utils as utils


class GetForwardingRules(utils.ForwardingRulesFetcher,
                         base_classes.BaseGetter):
  """Display detailed information about forwarding rules."""

  @staticmethod
  def Args(parser):
    base_classes.BaseGetter.Args(parser)
    utils.ForwardingRulesFetcher.Args(parser)
    base_classes.AddFieldsFlag(parser, 'forwardingRules')


GetForwardingRules.detailed_help = {
    'brief': 'Display detailed information about forwarding rules',
    'DESCRIPTION': """\
        *{command}* displays all data associated with forwarding rules
        in a project.
        """,
    'EXAMPLES': """\
        To get all forwarding rules in a project, run:

          $ {command}

        To get detailed information about a forwarding named
        ``my-forwarding-rule'', run:

          $ {command} my-forwarding-rule

        To get all of the global forwarding rules in a project, run:

          $ {command} --global

        To get all of the regional forwarding rules in a project, run:

          $ {command} --regions

        To get all of the forwarding rules from the ``us-central1'' and the
        ``europe-west1'' regions, run:

          $ {command} --regions us-central1 europe-west1
        """,

}
