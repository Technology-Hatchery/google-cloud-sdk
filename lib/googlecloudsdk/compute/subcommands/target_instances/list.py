# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing target instances."""
from googlecloudsdk.compute.lib import base_classes


class List(base_classes.ZonalLister):
  """List target instances."""

  @property
  def service(self):
    return self.context['compute'].targetInstances

  @property
  def print_resource_type(self):
    return 'targetInstances'


List.detailed_help = {
    'brief': 'List target instances',
    'DESCRIPTION': """\
        *{command}* lists summary information for the target
        instances in a project. The ``--uri'' option can be used to
        display the URIs for the target instances. Users who want
        to see more data should use ``gcloud compute target-instances
        get''.

        By default, target instances from all zones are listed. The
        results can be narrowed down by providing ``--zone''.
        """,
}
