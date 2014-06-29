# Copyright 2014 Google Inc. All Rights Reserved.
"""Common classes and functions for images."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import constants
from googlecloudsdk.compute.lib import lister
from googlecloudsdk.core import properties


class ImageResourceFetcher(object):
  """Mixin class for displaying images."""

  def GetResources(self, args, errors):
    """Yields images from (potentially) multiple projects."""
    filter_expression = lister.ConstructNameFilterExpression(args.name_regex)

    requests = [
        (self.service,
         messages.ComputeImagesListRequest(
             filter=filter_expression,
             maxResults=constants.MAX_RESULTS_PER_PAGE,
             project=properties.VALUES.core.project.Get(required=True))),
    ]

    if not args.no_standard_images:
      for project in constants.IMAGE_PROJECTS:
        requests.append(
            (self.service,
             messages.ComputeImagesListRequest(
                 filter=filter_expression,
                 maxResults=constants.MAX_RESULTS_PER_PAGE,
                 project=project)))

    images = lister.BatchList(
        requests=requests,
        http=self.context['http'],
        batch_url=self.context['batch-url'],
        errors=errors)

    for image in images:
      if not image.deprecated or args.show_deprecated:
        yield image


def AddImageFetchingArgs(parser):
  """Adds common flags for getting and listing images."""
  parser.add_argument(
      '--show-deprecated',
      action='store_true',
      help='If provided, deprecated images are shown.')

  no_standard_images = parser.add_argument(
      '--no-standard-images',
      action='store_true',
      help='If provided, images from well-known image projects are not shown.')
  no_standard_images.detailed_help = """\
     If provided, images from well-known image projects are not
     shown. The well known image projects are: {0}.
     """.format(', '.join(constants.IMAGE_PROJECTS))


def ExpandImage(image, uri_builder):
  """Returns a URI for the given image; also performs alias expansion."""
  image = image or constants.DEFAULT_IMAGE
  if image.startswith('https://'):
    return image

  image_spec = constants.IMAGE_ALIASES.get(image)
  if image_spec:
    project, image = image_spec
  else:
    project = None

  return uri_builder.Build('global', 'images', image, project=project)


def GetImageAliasTable():
  """Returns help text that explains the image aliases."""
  # Note: The leading spaces are very important in this string. The
  # final help text is dedented, so if the leading spaces are off, the
  # help will not be generated properly.
  return """The value for this option can be the name of an image in the
          current project, a URI when referring to an image in another
          project, or an alias from the table below.
          +
          [options="header",format="csv",grid="none",frame="none"]
          |========
          Alias,Project,Image Name,
          {0}
          |========
          +
          As new images are released, these aliases will be updated. If
          using this tool in a script where depending on a specific
          version of an image is necessary, then do not use the
          aliases. Instead, use the URI of the desired image.
          +
          Aliases are expanded first, so avoid creating images in
          your project whose names are in the set of aliases. If you
          do create an image whose name matches an alias, you can
          refer to it by using its URI.""".format(
              '\n          '.join(
                  ','.join([alias, project, image_name])
                  for alias, (project, image_name) in
                  sorted(constants.IMAGE_ALIASES.iteritems())))
