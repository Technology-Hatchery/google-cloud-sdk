# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting the project."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import batch_helper
from googlecloudsdk.core import properties


class Get(base_classes.BaseGetter):
  """Get the Google Compute Engine project resource."""

  @staticmethod
  def Args(parser):
    base_classes.BaseGetter.Args(parser, add_name_regex_arg=False)
    base_classes.AddFieldsFlag(parser, 'projects')

  @property
  def service(self):
    return self.context['compute'].projects

  @property
  def print_resource_type(self):
    return 'projects'

  def GetResources(self, args, errors):
    resources, request_errors = batch_helper.MakeRequests(
        requests=[
            (self.service,
             'Get',
             messages.ComputeProjectsGetRequest(
                 project=properties.VALUES.core.project.Get(required=True)))],
        http=self.context['http'],
        batch_url=self.context['batch-url'])
    errors.extend(request_errors)
    return resources


Get.detailed_help = {
    'brief': 'Get the Google Compute Engine project resource',
    'DESCRIPTION': """\
        *{command}* displays all data associated with the Google
        Compute Engine project resource. The project resource contains
        data such as global quotas, common instance metadata, and the
        project's creation time.
        """,
}

