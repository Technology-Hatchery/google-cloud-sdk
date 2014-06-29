# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for listing instances."""
from googlecloudsdk.compute.lib import base_classes


class ListInstances(base_classes.ZonalLister):
  """List Google Compute Engine virtual machine instances."""

  @property
  def service(self):
    return self.context['compute'].instances

  @property
  def print_resource_type(self):
    return 'instances'


ListInstances.detailed_help = {
    'brief': 'List Google Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* lists summary information for the virtual
        machine instances in a project. The ``--uri'' option can be used
        to display the URIs of the instances' in the project.
        Users who want to see more data should use ``gcloud compute
        instances get''.

        By default, instances from all zones are listed. The results can
        be narrowed down by providing ``--zone''.
        """,
}
