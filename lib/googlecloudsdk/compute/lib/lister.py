# Copyright 2014 Google Inc. All Rights Reserved.
"""Facilities for getting a list of Cloud resources."""
import copy
import itertools

from googlecloudapis.apitools.base.py import encoding
from googlecloudsdk.compute.lib import batch_helper
from googlecloudsdk.compute.lib import constants
from googlecloudsdk.compute.lib import property_selector


def BatchList(requests, http, batch_url, errors):
  """Makes a series of batch requests.

  If any response leads to an exception, that exception is raised.

  Args:
    requests: A list of requests to make. Each element must be a 2-element
      tuple where the first element is the service, and the second element
      is a protocol buffer representing the request.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Yields:
    Resources encapsulated as protocol buffers as they are received
      from the server.
  """
  while requests:
    batch_requests = [(service, 'List', protobuf)
                      for service, protobuf in requests]

    responses, request_errors = batch_helper.MakeRequests(
        requests=batch_requests,
        http=http,
        batch_url=batch_url)
    errors.extend(request_errors)

    new_requests = []

    for i, response in enumerate(responses):
      if not response:
        continue

      for item in response.items:
        yield item

      next_page_token = response.nextPageToken
      if next_page_token:
        new_request = copy.deepcopy(requests[i])
        new_request.pageToken = next_page_token
        new_requests.append(new_request)

    requests = new_requests


def _GetCmpFunc(col):
  """Returns a comparison function for sorted().

  The function is intended for comparing protocol buffers representing
  Cloud resources.

  If the property chosen for comparison does not exist in the resource,
  the property will be placed after a resource with the property in the
  non-decreasing order.

  Args:
    col: The property to compare proto buffers by. This should be a
      string presenting Python code that would be used to access the
      property (e.g., "disks[0].name"). If prefixed with "-", a
      non-increasing order is imposed.

  Returns:
    A comparison function.
  """
  if col.startswith('~'):
    col = col[1:]
    descending = True
  else:
    descending = False

  field_getter = property_selector.PropertyGetter(col)

  def Cmp(r1, r2):
    """A comparison function."""
    v1 = field_getter.Get(r1)
    v2 = field_getter.Get(r2)

    retval = cmp(v1, v2)

    # We want None to have the highest ordering, so if either value is
    # None, we have to negate the result of cmp().
    if v1 is None or v2 is None:
      retval *= -1

    if descending:
      return retval * -1
    else:
      return retval

  return Cmp


def _ConvertProtobufsToDicts(resources):
  for resource in resources:
    if resource is None:
      continue

    yield encoding.MessageToDict(resource)


def ProcessResults(resources, field_selector, sort_by=None, limit=None):
  resources = _ConvertProtobufsToDicts(resources)
  if sort_by:
    resources = sorted(resources, cmp=_GetCmpFunc(sort_by))

  if limit > 0:
    resources = itertools.islice(resources, limit)

  for resource in resources:
    if field_selector:
      yield field_selector.Apply(resource)
    else:
      yield resource


def ConstructNameFilterExpression(requested_name_regexes):
  """Construct a name filter expression.

  Args:
    requested_name_regexes: A list of name regular expressions that can
      be used to filter the resources by name on the server side.

  Returns:
    A string expression suitable for the requested names, or None if
    requested_name_regexes is None.
  """
  if requested_name_regexes:
    if len(requested_name_regexes) == 1:
      return 'name eq {0}'.format(requested_name_regexes[0])
    else:
      regexes = []
      for regex in requested_name_regexes:
        regexes.append('({0})'.format(regex))
      return 'name eq {0}'.format('|'.join(regexes))
  else:
    return None


def GetZonalResources(zones_service, resource_service, project, requested_zones,
                      requested_name_regexes, http, batch_url, errors):
  """Lists resources that are scoped by zone.

  Args:
    zones_service: An object with a List method that can list Compute
      Engine zone resources.
    resource_service: An object with a List method that can list Compute
      Engine resources of interest (e.g., instances).
    project: The Compute Engine project name for which listing should be
      performed.
    requested_zones: A list of zone names that can be used to control
      the scope of the list call.
    requested_name_regexes: A list of name regular expressions that can
      be used to filter the resources by name on the server side.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A generator that yields JSON-serializable dicts representing the results.
  """
  if requested_zones:
    zone_names = requested_zones
  else:
    zones = list(BatchList(
        requests=[(zones_service,
                   zones_service.GetRequestType('List')(project=project))],
        http=http,
        batch_url=batch_url,
        errors=errors))
    zone_names = [zone.name for zone in zones]

  filter_expression = ConstructNameFilterExpression(requested_name_regexes)

  list_requests = []
  for zone_name in zone_names:
    list_requests.append(
        (resource_service,
         resource_service.GetRequestType('List')(
             filter=filter_expression,
             project=project,
             zone=zone_name,
             maxResults=constants.MAX_RESULTS_PER_PAGE)))

  return BatchList(
      requests=list_requests,
      http=http,
      batch_url=batch_url,
      errors=errors)


def GetRegionalResources(regions_service, resource_service, project,
                         requested_regions, requested_name_regexes, http,
                         batch_url, errors):
  """Lists resources that are scoped by region.

  Args:
    regions_service: An object with a List method that can list Compute
      Engine region resources.
    resource_service: An object with a List method that can list Compute
      Engine resources of interest (e.g., targetPools).
    project: The Compute Engine project name for which listing should be
      performed.
    requested_regions: A list of region names that can be used to
      control the scope of the list call.
    requested_name_regexes: A list of name regular expressions that can
      be used to filter the resources by name on the server side.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A generator that yields JSON-serializable dicts representing the results.
  """
  if requested_regions:
    region_names = requested_regions
  else:
    regions = BatchList(
        requests=[(regions_service,
                   regions_service.GetRequestType('List')(project=project))],
        http=http,
        batch_url=batch_url,
        errors=errors)
    region_names = [region.name for region in regions]

  filter_expression = ConstructNameFilterExpression(requested_name_regexes)

  list_requests = []
  for region_name in region_names:
    list_requests.append(
        (resource_service,
         resource_service.GetRequestType('List')(
             filter=filter_expression,
             project=project,
             region=region_name,
             maxResults=constants.MAX_RESULTS_PER_PAGE)))

  return BatchList(
      requests=list_requests,
      http=http,
      batch_url=batch_url,
      errors=errors)


def GetGlobalResources(resource_service, project, requested_name_regexes, http,
                       batch_url, errors):
  """Lists resources in the global scope.


  Args:
    resource_service: An object with a List method that can list globally
      scoped Compute Engine resources of interest (e.g., networks).
    project: The Compute Engine project name for which listing should be
      performed.
    requested_name_regexes: A list of name regular expressions that can
      be used to filter the resources by name on the server side.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A generator that yields JSON-serializable dicts representing the results.
  """
  filter_expression = ConstructNameFilterExpression(requested_name_regexes)

  list_requests = [
      (resource_service,
       resource_service.GetRequestType('List')(
           filter=filter_expression,
           project=project,
           maxResults=constants.MAX_RESULTS_PER_PAGE))]

  return BatchList(
      requests=list_requests,
      http=http,
      batch_url=batch_url,
      errors=errors)
