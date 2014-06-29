# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for modifying backend services."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class Edit(base_classes.BaseEdit):
  """Modify backend services."""

  @staticmethod
  def Args(parser):
    base_classes.BaseEdit.Args(parser)
    parser.add_argument(
        'name',
        help='The name of the backend service to modify.')

  @property
  def service(self):
    return self.context['compute'].backendServices

  @property
  def print_resource_type(self):
    return 'backendServices'

  @property
  def example_resource(self):
    uri_prefix = ('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/')
    resource_views_uri_prefix = (
        'https://www.googleapis.com/resourceviews/v1beta1/projects/'
        'my-project/zones/')

    return messages.BackendService(
        backends=[
            messages.Backend(
                balancingMode=(
                    messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(
                    resource_views_uri_prefix +
                    'us-central1-a/resourceViews/group-1'),
                maxRate=100),
            messages.Backend(
                balancingMode=(
                    messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(
                    resource_views_uri_prefix +
                    'europe-west1-a/resourceViews/group-2'),
                maxRate=150),
        ],
        description='My backend service',
        healthChecks=[
            uri_prefix + 'global/httpHealthChecks/my-health-check'
        ],
        name='backend-service',
        port=80,
        selfLink=uri_prefix + 'global/backendServices/backend-service',
        timeoutSec=30,
    )

  def GetGetRequest(self, args):
    return (
        self.service,
        'Get',
        messages.ComputeBackendServicesGetRequest(
            project=self.context['project'],
            backendService=args.name))

  def GetSetRequest(self, args, replacement, _):
    return (
        self.service,
        'Update',
        messages.ComputeBackendServicesUpdateRequest(
            project=self.context['project'],
            backendService=args.name,
            backendServiceResource=replacement))


Edit.detailed_help = {
    'brief': 'Modify backend services',
    'DESCRIPTION': """\
        *{command}* can be used to modify a backend service. The backend
        service resource is fetched from the server and presented in a text
        editor. After the file is saved and closed, this command will
        update the resource. Only fields that can be modified are
        displayed in the editor.

        The editor used to modify the resource is chosen by inspecting
        the ``EDITOR'' environment variable.
        """,
}
