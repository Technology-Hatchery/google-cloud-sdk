# Copyright 2014 Google Inc. All Rights Reserved.
"""Common classes and functions for firewalls."""
import re

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import exceptions as calliope_exceptions

ALLOWED_METAVAR = 'PROTOCOL[:PORT[-PORT]]'
LEGAL_SPECS = re.compile(
    r"""

    (?P<protocol>[a-zA-Z0-9+.-]+) # The protocol group.

    (:(?P<ports>\d+(-\d+)?))?     # The optional ports group.
                                  # May specify a range.

    $                             # End of input marker.
    """,
    re.VERBOSE)


def ParseAllowed(allowed):
  """Parses protocol:port mappings from --allow command line."""
  allowed_value_list = []
  for spec in allowed or []:
    match = LEGAL_SPECS.match(spec)
    if not match:
      raise calliope_exceptions.ToolException(
          'firewall rules must be of the form {0}; received: {1}'
          .format(ALLOWED_METAVAR, spec))
    if match.group('ports'):
      ports = [match.group('ports')]
    else:
      ports = []
    allowed_value_list.append(messages.Firewall.AllowedValueListEntry(
        IPProtocol=match.group('protocol'),
        ports=ports))

  return allowed_value_list

