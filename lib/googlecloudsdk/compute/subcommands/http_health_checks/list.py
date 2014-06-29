# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing HTTP health checks."""
from googlecloudsdk.compute.lib import base_classes


class ListHttpHealthChecks(base_classes.GlobalLister):
  """List HTTP health checks."""

  @property
  def service(self):
    return self.context['compute'].httpHealthChecks

  @property
  def print_resource_type(self):
    return 'httpHealthChecks'


ListHttpHealthChecks.detailed_help = {
    'brief': 'List HTTP health checks',
    'DESCRIPTION': """\
        *{command}* lists summary information for the HTTP health
        checks in a project. The ``--uri'' option can be used to display
        the URIs of the HTTP health checks in the project.
        Users who want to see more data should use ``gcloud compute
        http-health-checks get''.
        """,
}
