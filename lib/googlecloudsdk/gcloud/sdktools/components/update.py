# Copyright 2013 Google Inc. All Rights Reserved.

"""The command to install/update gcloud components."""

import argparse

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.updater import update_manager


class Update(base.Command):
  """Command to update existing or install new components.

  Download and install Cloud SDK components, along with any other components
  they might depend on.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'component_ids',
        metavar='COMPONENT-IDS',
        nargs='*',
        help='The component IDs to update or install.')
    parser.add_argument(
        '--allow-no-backup',
        required=False,
        action='store_true',
        help=argparse.SUPPRESS)

  @exceptions.RaiseToolExceptionInsteadOf(update_manager.Error)
  def Run(self, args):
    """Runs the list command."""

    self.group.update_manager.Update(
        args.component_ids, allow_no_backup=args.allow_no_backup)
