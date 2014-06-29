# Copyright 2014 Google Inc. All Rights Reserved.
"""Annotates the resource types with extra information."""
import collections
import httplib

import protorpc
from googlecloudapis.compute.v1 import compute_v1_messages
from googlecloudsdk.compute.lib import path_simplifier
from googlecloudsdk.compute.lib import property_selector



def _FirewallRulesToCell(firewall):
  """Returns a compact string describing the firewall rules."""
  rules = []
  for allowed in firewall.get('allowed', []):
    protocol = allowed.get('IPProtocol')
    if not protocol:
      continue

    port_ranges = allowed.get('ports')
    if port_ranges:
      for port_range in port_ranges:
        rules.append('{0}:{1}'.format(protocol, port_range))
    else:
      rules.append(protocol)

  return ','.join(rules)


def _TargetPoolHealthChecksToCell(target_pool):
  """Comma-joins the names of health checks of the given target pool."""
  return ','.join(path_simplifier.Name(check) for check in
                  target_pool.get('healthChecks', []))


def _FirewallSourceRangesToCell(firewall):
  """Comma-joins the source ranges of the given firewall."""
  return ','.join(firewall.get('sourceRanges', []))


def _FirewallSourceTagsToCell(firewall):
  """Comma-joins the source tags of the given firewall."""
  return ','.join(firewall.get('sourceTags', []))


def _FirewallTargetTagsToCell(firewall):
  """Comma-joins the target tags of the given firewall."""
  return ','.join(firewall.get('targetTags', []))


def _NextMaintenanceToCell(zone):
  """Returns the start time of the next maintenance or ''."""
  maintenance_events = zone.get('maintenanceWindows', [])
  if maintenance_events:
    next_event = min(maintenance_events, key=lambda x: x.get('beginTime'))
    return next_event.get('beginTime') + '--' + next_event.get('endTime')
  else:
    return ''


def _QuotaToCell(metric, is_integer=True):
  """Returns a function that can format the given quota as usage/limit."""

  def QuotaToCell(region):
    """Formats the metric from the parent function."""
    for quota in region.get('quotas', []):
      if quota.get('metric') != metric:
        continue

      if is_integer:
        return '{0:6}/{1}'.format(
            int(quota.get('usage')),
            int(quota.get('limit')))
      else:
        return '{0:7.2f}/{1:.2f}'.format(
            quota.get('usage'),
            quota.get('limit'))

    return ''

  return QuotaToCell


def _MachineTypeMemoryToCell(machine_type):
  """Returns the memory of the given machine type in GB."""
  memory = machine_type.get('memoryMb')
  if memory:
    return '{0:5.2f}'.format(memory / 2.0 ** 10)
  else:
    return ''


def _OperationHttpStatusToCell(operation):
  """Returns the HTTP response code of the given operation."""
  if operation.get('status') == 'DONE':
    return operation.get('httpErrorStatusCode') or httplib.OK
  else:
    return ''


def _ImageSelfLinkToCell(image):
  """Shortens the image's self link."""
  self_link = image.get('selfLink')
  if self_link:
    return path_simplifier.ProjectSuffix(self_link)
  else:
    return ''


def _BackendsToCell(backend_service):
  """Comma-joins the names of the backend services."""
  return ','.join(backend.get('group')
                  for backend in backend_service.get('backends', []))


def _ProtobufDefinitionToFields(message_class):
  """Flattens the fields in a protocol buffer definition.

  For example, given the following definition:

    message Point {
      required int32 x = 1;
      required int32 y = 2;
      optional string label = 3;
    }

    message Polyline {
      repeated Point point = 1;
      optional string label = 2;
    }

  a call to this function with the Polyline class would produce:

    ['label',
     'point[].label',
     'point[].x',
     'point[].y']

  Args:
    message_class: A class that inherits from protorpc.messages.Message
        and defines a protocol buffer.

  Yields:
    The flattened fields, in non-decreasing order.
  """
  for field in sorted(message_class.all_fields(), key=lambda field: field.name):
    if isinstance(field, protorpc.messages.MessageField):
      for remainder in _ProtobufDefinitionToFields(field.type):
        if field.repeated:
          yield field.name + '[].' + remainder
        else:
          yield field.name + '.' + remainder
    else:
      if field.repeated:
        yield field.name + '[]'
      else:
        yield field.name


_InternalSpec = collections.namedtuple(
    'Spec', ['message_class', 'table_cols', 'transformations', 'editables'])

_SPECS = {
    'addresses': _InternalSpec(
        message_class=compute_v1_messages.Address,
        table_cols=[
            ('name', 'name'),
            ('status', 'status'),
            ('region', 'region'),
            ('address', 'address'),
        ],
        transformations=[
            ('region', path_simplifier.Name),
            ('users[]', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'disks': _InternalSpec(
        message_class=compute_v1_messages.Disk,
        table_cols=[
            ('name', 'name'),
            ('status', 'status'),
            ('sizeGb', 'sizeGb'),
            ('zone', 'zone'),
        ],
        transformations=[
            ('sourceSnapshot', path_simplifier.Name),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'firewalls': _InternalSpec(
        message_class=compute_v1_messages.Firewall,
        table_cols=[
            ('name', 'name'),
            ('network', 'network'),
            ('sourceRanges', _FirewallSourceRangesToCell),
            ('rules', _FirewallRulesToCell),
            ('sourceTags', _FirewallSourceTagsToCell),
            ('targetTags', _FirewallTargetTagsToCell),
        ],
        transformations=[
            ('network', path_simplifier.Name),
        ],
        editables=None,
    ),

    'forwardingRules': _InternalSpec(
        message_class=compute_v1_messages.ForwardingRule,
        table_cols=[
            ('name', 'name'),
            ('region', 'region'),
            ('IPAddress', 'IPAddress'),
            ('IPProtocol', 'IPProtocol'),
            ('target', 'target'),
        ],
        transformations=[
            ('region', path_simplifier.Name),
            ('target', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'httpHealthChecks': _InternalSpec(
        message_class=compute_v1_messages.HttpHealthCheck,
        table_cols=[
            ('name', 'name'),
            ('host', 'host'),
            ('port', 'port'),
            ('requestPath', 'requestPath'),
        ],
        transformations=[
            ],
        editables=None,
    ),

    'images': _InternalSpec(
        message_class=compute_v1_messages.Image,
        table_cols=[
            ('uri', _ImageSelfLinkToCell),
            ('status', 'status'),
            ('deprecated.state', 'deprecated.state'),
        ],
        transformations=[
            ],
        editables=None,
    ),

    'instances': _InternalSpec(
        message_class=compute_v1_messages.Instance,
        table_cols=[
            ('name', 'name'),
            ('status', 'status'),
            ('zone', 'zone'),
            ('machineType', 'machineType'),
            ('internalIP', 'networkInterfaces[0].networkIP'),
            ('externalIP', 'networkInterfaces[0].accessConfigs[0].natIP'),
        ],
        transformations=[
            ('disks[].source', path_simplifier.Name),
            ('machineType', path_simplifier.Name),
            ('networkInterfaces[].network', path_simplifier.Name),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'machineTypes': _InternalSpec(
        message_class=compute_v1_messages.MachineType,
        table_cols=[
            ('name', 'name'),
            ('zone', 'zone'),
            ('guestCpus', 'guestCpus'),
            ('memoryGb', _MachineTypeMemoryToCell),
            ('deprecated.state', 'deprecated.state'),
        ],
        transformations=[
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'networks': _InternalSpec(
        message_class=compute_v1_messages.Network,
        table_cols=[
            ('name', 'name'),
            ('IPv4Range', 'IPv4Range'),
            ('gatewayIPv4', 'gatewayIPv4'),
        ],
        transformations=[
            ],
        editables=None,
    ),

    'projects': _InternalSpec(
        message_class=compute_v1_messages.Project,
        table_cols=[],  # We do not support listing projects since
        # there is only one project (and there is no
        # API support).
        transformations=[
            ],
        editables=None,
    ),

    'operations': _InternalSpec(
        message_class=compute_v1_messages.Operation,
        table_cols=[
            ('name', 'name'),
            ('status', 'status'),
            ('httpStatus', _OperationHttpStatusToCell),
            ('operationType', 'operationType'),
            ('targetLink', 'targetLink'),
        ],
        transformations=[
            ('region', path_simplifier.Name),
            ('targetLink', path_simplifier.ScopedSuffix),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'regions': _InternalSpec(
        message_class=compute_v1_messages.Region,
        table_cols=[
            ('name', 'name'),
            ('status', 'status'),
            ('cpus', _QuotaToCell('CPUS', is_integer=False)),
            ('disksGb', _QuotaToCell('DISKS_TOTAL_GB', is_integer=True)),
            ('addresses', _QuotaToCell('IN_USE_ADDRESSES', is_integer=True)),
            ('reservedAddresses',
             _QuotaToCell('STATIC_ADDRESSES', is_integer=True)),
        ],
        transformations=[
            ('zones[]', path_simplifier.Name),
        ],
        editables=None,
    ),

    'routes': _InternalSpec(
        message_class=compute_v1_messages.Route,
        table_cols=[
            ('name', 'name'),
            ('network', 'network'),
            ('destRange', 'destRange'),
            ('nextHopInstance', 'nextHopInstance'),
            ('nextHopIp', 'nextHopIp'),
            ('nextHopGateway', 'nextHopGateway'),
            ('priority', 'priority'),
        ],
        transformations=[
            ('network', path_simplifier.Name),
            ('nextHopInstance', path_simplifier.ScopedSuffix),
            ('nextHopGateway', path_simplifier.Name),
        ],
        editables=None,
    ),

    'snapshots': _InternalSpec(
        message_class=compute_v1_messages.Snapshot,
        table_cols=[
            ('name', 'name'),
            ('status', 'status'),
            ('diskSizeGb', 'diskSizeGb'),
            ('sourceDisk', 'sourceDisk'),
        ],
        transformations=[
            ('sourceDisk', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'targetPools': _InternalSpec(
        message_class=compute_v1_messages.TargetPool,
        table_cols=[
            ('name', 'name'),
            ('region', 'region'),
            ('sessionAffinity', 'sessionAffinity'),
            ('backupPool', 'backupPool'),
            ('healthChecks', _TargetPoolHealthChecksToCell),
        ],
        transformations=[
            ('backupPool', path_simplifier.Name),
            ('healthChecks[]', path_simplifier.Name),
            ('instances[]', path_simplifier.ScopedSuffix),
            ('region', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetPoolInstanceHealth': _InternalSpec(
        message_class=compute_v1_messages.TargetPoolInstanceHealth,
        table_cols=[
            ],
        transformations=[
            ('healthStatus[].instance', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'targetInstances': _InternalSpec(
        message_class=compute_v1_messages.TargetInstance,
        table_cols=[
            ('name', 'name'),
            ('zone', 'zone'),
            ('natPolicy', 'natPolicy'),
            ('instance', 'instance'),
        ],
        transformations=[
            ('instance', path_simplifier.ScopedSuffix),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'zones': _InternalSpec(
        message_class=compute_v1_messages.Zone,
        table_cols=[
            ('name', 'name'),
            ('region', 'region'),
            ('status', 'status'),
            ('nextMaintenance', _NextMaintenanceToCell),
        ],
        transformations=[
            ('region', path_simplifier.Name),
        ],
        editables=None,
    ),

    'backendServices': _InternalSpec(
        message_class=getattr(compute_v1_messages, 'BackendService', None),
        table_cols=[
            ('name', 'name'),
            ('backends', _BackendsToCell),
        ],
        transformations=[
            ('healthChecks[]', path_simplifier.Name),
            ('backends[].group', path_simplifier.ScopedSuffix),
        ],
        editables=[
            'backends',
            'description',
            'healthChecks',
            'port',
            'timeoutSec',
        ],
    ),

    'backendServiceGroupHealth': _InternalSpec(
        message_class=compute_v1_messages.BackendServiceGroupHealth,
        table_cols=[
            ],
        transformations=[
            ('healthStatus[].instance', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'urlMaps': _InternalSpec(
        message_class=getattr(compute_v1_messages, 'UrlMap', None),
        table_cols=[
            ('name', 'name'),
            ('defaultService', 'defaultService'),
        ],
        transformations=[
            ('defaultService', path_simplifier.Name),
            ('pathMatchers[].defaultService', path_simplifier.Name),
            ('pathMatchers[].pathRules[].service', path_simplifier.Name),
            ('tests[].service', path_simplifier.Name),
        ],
        editables=[
            'defaultService',
            'description',
            'hostRules',
            'pathMatchers',
            'tests',
        ],
    ),

    'targetHttpProxies': _InternalSpec(
        message_class=getattr(
            compute_v1_messages, 'TargetHttpProxy', None),
        table_cols=[
            ('name', 'name'),
            ('urlMap', 'urlMap'),
        ],
        transformations=[
            ('urlMap', path_simplifier.Name),
        ],
        editables=[
        ],
    ),
}

Spec = collections.namedtuple(
    'Spec',
    ['message_class', 'fields', 'table_cols', 'transformations', 'editables'])


def GetSpec(resource_type):
  """Returns a Spec for the given resource type."""
  spec = _SPECS[resource_type]

  table_cols = []
  for name, action in spec.table_cols:
    if isinstance(action, basestring):
      table_cols.append((name, property_selector.PropertyGetter(action)))
    elif callable(action):
      table_cols.append((name, action))
    else:
      raise ValueError('expected function or property in table_cols list: {0}'
                       .format(spec))

  fields = list(_ProtobufDefinitionToFields(spec.message_class))
  return Spec(message_class=spec.message_class,
              fields=fields,
              table_cols=table_cols,
              transformations=spec.transformations,
              editables=spec.editables)
