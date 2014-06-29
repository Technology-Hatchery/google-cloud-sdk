# Copyright 2014 Google Inc. All Rights Reserved.
"""Common classes and functions for operations."""
import itertools

from googlecloudsdk.compute.lib import lister
from googlecloudsdk.core import properties


class OperationsResourceFetcherMixin(object):
  """Mixin class for operation resources."""

  def GetResources(self, args, errors):
    """Get operations in all scopes."""
    generators = []
    show_all = all([getattr(args, 'global') is None,
                    args.zones is None,
                    args.regions is None])
    compute = self.context['compute']

    if getattr(args, 'global') or show_all:
      generators.append(lister.GetGlobalResources(
          resource_service=self.context['compute'].globalOperations,
          project=properties.VALUES.core.project.Get(required=True),
          requested_name_regexes=args.name_regex,
          http=self.context['http'],
          batch_url=self.context['batch-url'],
          errors=errors))

    if args.regions is not None or show_all:
      generators.append(lister.GetRegionalResources(
          regions_service=compute.regions,
          resource_service=self.context['compute'].regionOperations,
          project=properties.VALUES.core.project.Get(required=True),
          requested_regions=args.regions or [],
          requested_name_regexes=args.name_regex,
          http=self.context['http'],
          batch_url=self.context['batch-url'],
          errors=errors))

    if args.zones is not None or show_all:
      generators.append(lister.GetZonalResources(
          zones_service=compute.zones,
          resource_service=self.context['compute'].zoneOperations,
          project=properties.VALUES.core.project.Get(required=True),
          requested_zones=args.zones or [],
          requested_name_regexes=args.name_regex,
          http=self.context['http'],
          batch_url=self.context['batch-url'],
          errors=errors))

    return itertools.chain(*generators)


def AddOperationFetchingArgs(parser):
  """Adds common flags for getting and listing operations."""
  parser.add_argument(
      '--regions',
      metavar='REGION',
      help='If provided, operations from the given regions are queried.',
      nargs='*',
      default=None)
  parser.add_argument(
      '--zones',
      metavar='ZONE',
      help='If provided, operations from the given zones are queried.',
      nargs='*',
      default=None)
  parser.add_argument(
      '--global',
      action='store_true',
      help='If provided, operations from the global scope are queried.',
      default=None)
