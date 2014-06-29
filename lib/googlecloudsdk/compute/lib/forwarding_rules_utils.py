# Copyright 2014 Google Inc. All Rights Reserved.
"""Common classes and functions for forwarding rules."""
import abc

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import constants
from googlecloudsdk.compute.lib import lister
from googlecloudsdk.core import properties


class ForwardingRulesMutator(base_classes.BaseAsyncMutator):
  """Base class for modifying forwarding rules."""

  @staticmethod
  def Args(parser):
    """Adds common flags for mutating forwarding rules."""
    scope = parser.add_mutually_exclusive_group(required=True)

    region = scope.add_argument(
        '--region',
        help='The region of the forwarding rule.')
    region.detailed_help = """\
        The region of the forwarding rule. This is required for regional
        forwarding rules. A forwarding rule is regional if it references a
        target pool or a target instance.
        """

    global_flag = scope.add_argument(
        '--global',
        action='store_true',
        help='If provided, assume the forwarding rules are global.')
    global_flag.detailed_help = """\
        If provided, assume the forwarding rules are global.
        A forwarding rule is global if it references a target HTTP proxy.
        """

  @property
  def service(self):
    if self.global_request:
      return self.context['compute'].globalForwardingRules
    else:
      return self.context['compute'].forwardingRules

  @property
  def print_resource_type(self):
    return 'forwardingRules'

  @abc.abstractmethod
  def CreateGlobalRequests(self, args):
    """Return a list of one of more globally scoped request."""

  @abc.abstractmethod
  def CreateRegionalRequests(self, args):
    """Return a list of one of more regionally scoped request."""

  def CreateRequests(self, args):
    self.global_request = getattr(args, 'global')

    if self.global_request:
      return self.CreateGlobalRequests(args)
    else:
      return self.CreateRegionalRequests(args)


class ForwardingRulesTargetMutator(ForwardingRulesMutator):
  """Base class for modifying forwarding rule targets."""

  @staticmethod
  def Args(parser):
    """Adds common flags for mutating forwarding rule targets."""
    ForwardingRulesMutator.Args(parser)

    target = parser.add_mutually_exclusive_group(required=True)

    target_instance = target.add_argument(
        '--target-instance',
        help='The target instance that will receive the traffic.')
    target_instance.detailed_help = """\
        The name of the target instance that will receive the traffic.
        The target instance must be in a zone that's in the forwarding
        rule's region. When specifying a target instance, its zone must be
        specified using ``--target-instance-zone''. Global forwarding rules
        may not direct traffic to target instances.
        """

    target_pool = target.add_argument(
        '--target-pool',
        help='The target pool that will receive the traffic.')
    target_pool.detailed_help = """\
        The target pool that will receive the traffic. The target pool
        must be in the same region as the forwarding rule. Global
        forwarding rules may not direct traffic to target pools.
        """

    target.add_argument(
        '--target-http-proxy',
        help='The target HTTP proxy that will receive the traffic.')

    parser.add_argument(
        '--target-instance-zone',
        help='The zone of the target instance.')

    parser.add_argument(
        'name',
        help='The name of the forwarding rule.')

  def GetGlobalTargetUri(self, args):
    """Return the forwarding target for a globally scoped request."""

    if args.target_instance:
      raise exceptions.ToolException(
          'you cannot specify --target-instance for a global '
          'forwarding rule')
    if args.target_pool:
      raise exceptions.ToolException(
          'you cannot specify --target-pool for a global '
          'forwarding rule')

    return self.context['uri-builder'].Build(
        'global', 'targetHttpProxies', args.target_http_proxy)

  def GetRegionalTargetUri(self, args):
    """Return the forwarding target for a regionally scoped request."""

    if args.target_instance and not args.target_instance_zone:
      raise exceptions.ToolException(
          'you must specify --target-instance-zone when specifying '
          '--target-instance')
    if args.target_instance_zone and not args.target_instance:
      raise exceptions.ToolException(
          'you cannot specify --target-instance-zone unless you are specifying '
          '--target-instance')

    if args.target_pool:
      return self.context['uri-builder'].Build(
          'regions', args.region, 'targetPools', args.target_pool)
    elif args.target_instance:
      return self.context['uri-builder'].Build(
          'zones', args.target_instance_zone, 'targetInstances',
          args.target_instance)
    else:
      return self.context['uri-builder'].Build(
          'regions', args.region, 'targetHttpProxies', args.target_http_proxy)


class ForwardingRulesFetcher(object):
  """Mixin class for displaying forwarding rules.

  Derived classes must implement CreateGlobalRequests and
  CreateRegionalRequests.
  """

  @staticmethod
  def Args(parser):
    """Adds common flags for fetching forwarding rules."""
    parser.add_argument(
        '--regions',
        metavar='REGION',
        help='If provided, forwarding rules from the given regions are shown.',
        nargs='*',
        default=None)
    parser.add_argument(
        '--global',
        action='store_true',
        help='If provided, global forwarding rules are shown.',
        default=False)

  @property
  def print_resource_type(self):
    return 'forwardingRules'

  def GetResources(self, args, errors):
    """Yields regional and/or global forwarding rules."""
    filter_expression = lister.ConstructNameFilterExpression(args.name_regex)
    project = properties.VALUES.core.project.Get(required=True)
    compute = self.context['compute']

    show_all = not getattr(args, 'global') and (args.regions is None)

    requests = []

    if getattr(args, 'global') or show_all:
      requests.append(
          (compute.globalForwardingRules,
           messages.ComputeGlobalForwardingRulesListRequest(
               filter=filter_expression,
               maxResults=constants.MAX_RESULTS_PER_PAGE,
               project=project)))

    if args.regions is not None or show_all:
      if args.regions:
        region_names = args.regions
      else:
        regions = lister.BatchList(
            requests=[
                (compute.regions,
                 compute.regions.GetRequestType('List')(project=project))],
            http=self.context['http'],
            batch_url=self.context['batch-url'],
            errors=errors)
        region_names = [region.name for region in regions]

      for region_name in region_names:
        requests.append(
            (compute.forwardingRules,
             messages.ComputeForwardingRulesListRequest(
                 filter=filter_expression,
                 maxResults=constants.MAX_RESULTS_PER_PAGE,
                 region=region_name,
                 project=project)))

    forwarding_rules = lister.BatchList(
        requests=requests,
        http=self.context['http'],
        batch_url=self.context['batch-url'],
        errors=errors)

    for forwarding_rule in forwarding_rules:
      yield forwarding_rule
