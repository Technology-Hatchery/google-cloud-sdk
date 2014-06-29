# Copyright 2013 Google Inc. All Rights Reserved.

"""config command group."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import properties


class Config(base.Group):
  """View and edit Google Cloud SDK properties."""

  @staticmethod
  def PropertiesCompleter(prefix, parsed_args, **kwargs):
    section = parsed_args.section or properties.VALUES.default_section.name
    if section in properties.VALUES.AllSections():
      props = properties.VALUES.Section(section).AllProperties()
      return [p for p in props if p.startswith(prefix)]
