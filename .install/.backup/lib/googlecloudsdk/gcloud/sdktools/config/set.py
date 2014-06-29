# Copyright 2013 Google Inc. All Rights Reserved.

"""Command to set properties."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import properties


class Set(base.Command):
  """Edit Google Cloud SDK properties.

  Set the value for an option, so that Cloud SDK tools can use them as
  configuration.
  """

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        '--global-only',
        action='store_true',
        help='Set the option in the global properties file.')
    parser.add_argument(
        '--section', '-s',
        default=properties.VALUES.default_section.name,
        help='The section containing the option to be set.',
        choices=properties.VALUES.AllSections())
    property_arg = parser.add_argument(
        'property',
        help='The property to be set.')
    property_arg.completer = Set.group_class.PropertiesCompleter
    parser.add_argument(
        'value',
        help='The value to be set.')

  @c_exc.RaiseToolExceptionInsteadOf(properties.Error)
  def Run(self, args):
    """Runs this command."""
    prop = properties.VALUES.Section(args.section).Property(args.property)
    properties.PersistProperty(
        prop, args.value, force_global=args.global_only)
