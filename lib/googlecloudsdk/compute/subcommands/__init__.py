# Copyright 2014 Google Inc. All Rights Reserved.
"""The super-group for the compute CLI."""

import urlparse

from googlecloudapis.compute.v1 import compute_v1_client
from googlecloudsdk.calliope import base
from googlecloudsdk.compute.lib import constants
from googlecloudsdk.compute.lib import uri_builder
from googlecloudsdk.core import cli
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


class Compute(base.Group):
  """Read and manipulate Google Compute Engine resources."""

  def Filter(self, context, _):
    http = cli.Http()
    context['http'] = http

    project = properties.VALUES.core.project.Get(required=True)
    context['project'] = project

    api_host = properties.VALUES.core.api_host.Get()
    compute_url = urlparse.urljoin(api_host, 'compute/v1/')

    context['uri-builder'] = uri_builder.UriBuilder(
        compute_url, project=project)

    context['batch-url'] = urlparse.urljoin(api_host, 'batch')

    v1_compute = compute_v1_client.ComputeV1(
        url=compute_url,
        get_credentials=False,
        http=http)
    context['compute'] = v1_compute



Compute.detailed_help = {
    'brief': 'Read and manipulate Google Compute Engine resources',
}
