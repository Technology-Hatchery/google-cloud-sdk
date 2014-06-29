# Copyright 2014 Google Inc. All Rights Reserved.
"""A module for building URIs."""

import urlparse


class UriBuilder(object):
  """A class for building URIs.

  Example usage:

    >>> builder = UriBuilder(
        'https://googleapis.com/compute/v1',
        project='my-project')
    <UriBuilder object at ...>
    >>> builder.Build('zones', 'us-central1-a')
    'https://googleapis.com/compute/v1/projects/my-project/zones/us-central1-a'
    >>> builder.Build('zones', 'us-central1-a', project='other')
    'https://googleapis.com/compute/v1/projects/other/zones/us-central1-a'

  """

  def __init__(self, prefix, project):
    """Creates a new UriBuilder."""
    self._prefix = prefix
    self._project = project

  def Build(self, *parts, **kwargs):
    """Returns a URI with the given parts."""
    project = kwargs.get('project') or self._project
    return urlparse.urljoin(
        self._prefix,
        '/'.join(['projects', project] + list(parts)))
