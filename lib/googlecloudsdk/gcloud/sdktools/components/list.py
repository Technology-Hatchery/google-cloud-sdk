# Copyright 2013 Google Inc. All Rights Reserved.

"""The command to list installed/available gcloud components."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.updater import update_manager


class List(base.Command):
  """Command to list the current state of installed components.

  List all available components and indicate whether or not they're installed or
  have updates available.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--show-versions', required=False, action='store_true',
        help='Show version information for all components.')

  @exceptions.RaiseToolExceptionInsteadOf(update_manager.Error)
  def Run(self, args):
    """Runs the list command."""

    self.group.update_manager.List(show_versions=args.show_versions)
