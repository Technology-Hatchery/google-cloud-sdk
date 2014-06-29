# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing forwarding rules."""
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import forwarding_rules_utils as utils


class ListForwardingRules(utils.ForwardingRulesFetcher,
                          base_classes.BaseLister):
  """List forwarding rules."""

  @staticmethod
  def Args(parser):
    base_classes.BaseLister.Args(parser)
    utils.ForwardingRulesFetcher.Args(parser)


ListForwardingRules.detailed_help = {
    'brief': 'List forwarding rules',
    'DESCRIPTION': """\
        *{command}* lists summary information of forwarding rules in a
        project. The ``--uri'' option can be used to display URIs
        instead. Users who want to see more data should use ``gcloud
        compute forwarding-rules get''.

        By default, global forwarding rules and forwarding rules from
        all regions are listed. The results can be narrowed down by providing
        the ``--region'' and/or ``--global'' flags.
        """,
    'EXAMPLES': """\
        To list all forwarding rules in a project in table form, run:

          $ {command}

        To list the URIs of all forwarding rules in a project, run:

          $ {command} --uri

        To list all of the global forwarding rules in a project, run:

          $ {command} --global

        To list all of the regional forwarding rules in a project, run:

          $ {command} --regions

        To list all of the forwarding rules from the ``us-central1'' and the
        ``europe-west1'' regions, run:

          $ {command} --regions us-central1 europe-west1
        """,

}
