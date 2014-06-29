# Copyright 2014 Google Inc. All Rights Reserved.
"""Utilities for waiting on Compute Engine operations."""
import httplib
import logging

from googlecloudsdk.compute.lib import batch_helper
from googlecloudsdk.compute.lib import path_simplifier
from googlecloudsdk.compute.lib import time_utils

_POLLING_TIMEOUT_SEC = 60 * 5
_MAX_TIME_BETWEEN_POLLS_SEC = 5


def _RecordProblems(operation, warnings, errors):
  """Records any warnings and errors into the given lists."""
  for warning in operation.warnings or []:
    warnings.append(warning.message)
  if operation.error:
    for error in operation.error.errors or []:
      errors.append((operation.httpErrorStatusCode, error.message))


def _RecordUnfinishedOperations(operations, errors):
  """Adds error messages stating that the given operations timed out."""
  pending_resources = [operation.targetLink for operation in operations]
  errors.append((None,
                 'failed to {action} the following resources within '
                 '{timeout}s: {links}'.format(
                     action=operations[0].operationType,
                     timeout=_POLLING_TIMEOUT_SEC,
                     links=', '.join(pending_resources))))


def WaitForOperations(operations, project, operation_service, resource_service,
                      http, batch_url, warnings, errors,
                      custom_get_requests=None, timeout=None):
  """Blocks until the given operations are done or until a timeout is reached.

  Args:
    operations: A list of Operation objects to poll.
    project: The project to which the resources belog.
    operation_service: The service that can be used to get operation
      objects.
    resource_service: The service of the collection being mutated by
      the operations. If the operation type is not delete, this service
      is used to fetch the mutated objects after the operations are done.
    http: An HTTP object.
    batch_url: The URL to which batch requests should be sent.
    warnings: An output parameter for capturing warnings.
    errors: An output parameter for capturing errors.
    custom_get_requests: A mapping of resource names to requests. If
      this is provided, when an operation is DONE, instead of performing
      a get on the targetLink, this function will consult custom_get_requests
      and perform the request dictated by custom_get_requests.
    timeout: The maximum amount of time, in seconds, to wait for the
      operations to reach the DONE state.

  Yields:
    The resources pointed to by the operations' targetLink fields if
    the operation type is not delete. Only resources whose
    corresponding operations reach done are yielded.
  """
  timeout = timeout or _POLLING_TIMEOUT_SEC

  operation_type = operation_service.GetResponseType('Get')

  responses = []
  start = time_utils.CurrentTimeSec()
  sleep_sec = 0

  while operations:
    resource_requests = []
    operation_requests = []

    logging.debug('Operations to inspect: %s', operations)
    for operation in operations:
      if operation.status == operation_type.StatusValueValuesEnum.DONE:
        # The operation has reached the DONE state, so we record any
        # problems it contains (if any) and proceed to get the target
        # resource if there were no problems and the operation is not
        # a deletion.

        _RecordProblems(operation, warnings, errors)

        # We shouldn't attempt to get the target resource if there was
        # anything wrong with the operation. Note that
        # httpErrorStatusCode is set only when the operation is not
        # successful.
        if (operation.httpErrorStatusCode and
            operation.httpErrorStatusCode != httplib.OK):
          continue

        # Just in case the server did not set httpErrorStatusCode but
        # the operation did fail, we check the "error" field.
        if operation.error:
          continue

        # We shouldn't get the target resource if the operation type
        # is delete because there will be no resource left.
        if operation.operationType == 'delete':
          continue

        if custom_get_requests:
          resource_requests.append(custom_get_requests[operation.targetLink])
        else:
          request = resource_service.GetRequestType('Get')(project=project)
          if operation.zone:
            request.zone = path_simplifier.Name(operation.zone)
          elif operation.region:
            request.region = path_simplifier.Name(operation.region)
          name_field = resource_service.GetMethodConfig(
              'Get').ordered_params[-1]
          setattr(request, name_field,
                  path_simplifier.Name(operation.targetLink))
          resource_requests.append((resource_service, 'Get', request))

      else:
        # The operation has not reached the DONE state, so we add a
        # get request to poll the operation.
        request = operation_service.GetRequestType('Get')(
            operation=operation.name,
            project=project)
        if operation.zone:
          request.zone = path_simplifier.Name(operation.zone)
        elif operation.region:
          request.region = path_simplifier.Name(operation.region)
        operation_requests.append((operation_service, 'Get', request))

    requests = resource_requests + operation_requests
    if not requests:
      break

    responses, request_errors = batch_helper.MakeRequests(
        requests=requests,
        http=http,
        batch_url=batch_url)
    errors.extend(request_errors)

    operations = []
    for response in responses:
      if isinstance(response, operation_type):
        operations.append(response)
      else:
        yield response

    # If there are no more operations, we are done.
    if not operations:
      break

    # Did we time out? If so, record the operations that timed out so
    # they can be reported to the user.
    if time_utils.CurrentTimeSec() - start > timeout:
      logging.debug('Timeout of %ss reached.', timeout)
      _RecordUnfinishedOperations(operations, errors)
      break

    # Sleeps before trying to poll the operations again.
    sleep_sec += 1
    logging.debug('Sleeping for %ss.', sleep_sec)
    time_utils.Sleep(min(sleep_sec, _MAX_TIME_BETWEEN_POLLS_SEC))
