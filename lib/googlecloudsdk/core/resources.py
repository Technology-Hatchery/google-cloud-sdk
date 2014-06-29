# Copyright 2013 Google Inc. All Rights Reserved.

"""Manage resources for the cloud platform.

"""

import re
import urllib

from googlecloudapis.apitools.base.py import base_api
from googlecloudapis.apitools.base.py import util
from googlecloudsdk.core import exceptions


_COLLECTION_SUB_RE = r'[a-zA-Z]+\.[a-zA-Z]+'

_COLLECTIONPATH_RE = re.compile(r'(?:({collection})::)?(.+)'.format(
    collection=_COLLECTION_SUB_RE))
# The first two wildcards in this are the API and the API's version. The rest
# are parameters into a specific collection in that API/version.
_URL_RE = re.compile(r'(https://www.googleapis.com/[^/]+/[^/]+/)(.+)')
_METHOD_ID_RE = re.compile(r'({collection})\.get'.format(
    collection=_COLLECTION_SUB_RE))


class Error(Exception):
  """Exceptions for this module."""


class _ResourceWithoutGetException(Error):
  """Exception for resources with no Get method."""


class BadResolverException(Error):
  """Exception to signal that a resource has no Get method."""

  def __init__(self, param):
    super(BadResolverException, self).__init__(
        'bad resolver for [{param}]'.format(param=param))


class AmbiguousAPIException(Error):
  """Exception for when two APIs try to define a resource."""

  def __init__(self, collection, base_urls):
    super(AmbiguousAPIException, self).__init__(
        'collection [{collection}] defined in multiple APIs: {apis}'.format(
            collection=collection,
            apis=repr(base_urls)))


class UserError(exceptions.Error, Error):
  """Exceptions that are caused by user input."""


class InvalidResourceException(UserError):
  """A collection-path that was given could not be parsed."""

  def __init__(self, line):
    super(InvalidResourceException, self).__init__(
        'could not parse resource: [{line}]'.format(line=line))


class WrongProtocolException(UserError):
  """A collection-path that was given could not be parsed."""

  def __init__(self):
    super(WrongProtocolException, self).__init__(
        'http:// is not a supported protocol, use https:// instead')


class WrongResourceCollectionException(UserError):
  """A command line that was given had the wrong collection."""

  def __init__(self, expected, got):
    super(WrongResourceCollectionException, self).__init__(
        'wrong collection: expected [{expected}], got [{got}]'.format(
            expected=expected, got=got))


class TooManyFieldsException(UserError):
  """A command line that was given had too many fields."""

  def __init__(self, path, ordered_params):
    expected = '/'.join(['{'+p+'}' for p in ordered_params])
    got = path
    super(TooManyFieldsException, self).__init__(
        'too many fields: expected [{expected}], got [{got}]'.format(
            expected=expected, got=got))


class UnknownFieldException(UserError):
  """A command line that was given did not specify a field."""

  def __init__(self, collectionpath, expected):
    super(UnknownFieldException, self).__init__(
        'unknown field [{expected}] in [{path}]'.format(
            expected=expected, path=collectionpath))


class UnknownCollectionException(UserError):
  """A command line that was given did not specify a collection."""

  def __init__(self, line):
    super(UnknownCollectionException, self).__init__(
        'unknown collection for [{line}]'.format(line=line))


class InvalidCollectionException(UserError):
  """A command line that was given did not specify a collection."""

  def __init__(self, collection):
    super(InvalidCollectionException, self).__init__(
        'unknown collection [{collection}]'.format(collection=collection))


class UnresolvedParamException(Error):
  """A parameter's value was unresolved, despite a resolver being assigned."""

  def __init__(self, param):
    super(UnresolvedParamException, self).__init__(
        'unresolved field [{param}]'.format(param=param))


# TODO(user): Ensure that all the user-facing error messages help the
# user figure out what to do.


class _ResourceParser(object):
  """Class that turns command-line arguments into a cloud resource message.

  """

  def __init__(self, service, registry):
    try:
      self.registry = registry
      self.method_config = service.GetMethodConfig('Get')
      self.request_type = service.GetRequestType('Get')
      match = _METHOD_ID_RE.match(self.method_config.method_id)
      if not match:
        raise _ResourceWithoutGetException()
      self.collection = match.group(1)
      # pylint:disable=protected-access
      self.client = service._client
      self.service = service
    except KeyError:
      raise _ResourceWithoutGetException()

  def ParseCollectionPath(self, collectionpath, kwargs, resolve):
    """Given a command line and some keyword args, get the resource.

    Args:
      collectionpath: str, The human-typed collectionpath from the command line.
          Can be None to indicate all params should be taken from kwargs.
      kwargs: {str:str}, The flags available from context that can help
          parse this resource. If the fields in collectionpath do not provide
          all the necessary information, kwargs will be searched for what
          remains.
      resolve: bool, If True, call the resource's .Resolve() method before
          returning, ensuring that all of the resource parameters are defined.
          If False, don't call them, under the assumption that it will be called
          later.

    Returns:
      protorpc.messages.Message, The object containing info about this resource.

    Raises:
      InvalidResourceException: If the provided collectionpath is malformed.
      WrongResourceCollectionException: If the collectionpath specified the
          wrong collection.
      TooManyFieldsException: If the collectionpath's path provided too many
          fields.
      UnknownFieldException: If the collectionpath's path did not provide enough
          fields.
    """
    if collectionpath is not None:
      match = _COLLECTIONPATH_RE.match(collectionpath)
      if not match:
        # Right now it is impossible for this exception to be raised: the
        # regular expression matches all strings. But we will leave it in
        # in case that ever changes.
        raise InvalidResourceException(collectionpath)
      collection, path = match.groups()

      # TODO(user): Remove when we agree on collectionpaths.
      if collection is not None:
        raise InvalidResourceException(collectionpath)

      if collection and collection != self.collection:
        raise WrongResourceCollectionException(
            expected=self.collection, got=collection)

      fields = path.split('/')

      # TODO(user): Remove when we agree on collectionpaths.
      if len(fields) != 1:
        raise InvalidResourceException(collectionpath)

      num_missing = len(self.method_config.ordered_params) - len(fields)
      # Check if there were too many fields provided.
      if num_missing < 0:
        raise TooManyFieldsException(
            path=path, ordered_params=self.method_config.ordered_params)
      # pad the beginning with Nones so we don't have to count backwards.
      fields = [None] * num_missing + fields
    else:
      fields = [None] * len(self.method_config.ordered_params)

    # Build up the resource params from kwargs or the fields in the
    # collection-path.
    params = {}
    for param, field in zip(self.method_config.ordered_params, fields):
      params[param] = field

    request = self.request_type()
    for param in self.method_config.ordered_params:
      setattr(request, param, params[param])

    resource = Resource(
        self.collection, request, self.method_config.ordered_params, kwargs,
        collectionpath, self)

    if resolve:
      resource.Resolve()

    return resource

  def __str__(self):
    path_str = ''
    for param in self.method_config.ordered_params:
      path_str = '[{path}]/{param}'.format(path=path_str, param=param)
    return '[{collection}::]{path}'.format(
        collection=self.collection, path=path_str)


class Resource(object):
  """Information about a Cloud resource."""

  def __init__(self, collection, request, ordered_params, resolvers,
               collectionpath, parser):
    self.__collection = collection
    self.__request = request
    self.__self_link = None
    self.__ordered_params = ordered_params
    self.__resolvers = resolvers
    self.__collectionpath = collectionpath
    self.__parser = parser
    for param in ordered_params:
      setattr(self, param, getattr(request, param))

  def Collection(self):
    return self.__collection

  def SelfLink(self):
    self.Resolve()
    return self.__self_link

  def Request(self):
    return self.__request

  def Resolve(self):
    """Resolve unknown parameters for this resource.

    Raises:
      UnknownFieldException: If, after resolving, one of the fields is still
          unknown.
    """

    for param in self.__ordered_params:
      if getattr(self, param):
        continue

      def ResolveParam(value):
        if value is None:
          raise UnresolvedParamException(param)
        setattr(self, param, value)
        setattr(self.__request, param, value)

      # First try the resolvers given to this resource explicitly.
      resolver = self.__resolvers.get(param)
      if resolver:
        if callable(resolver):
          ResolveParam(resolver())
        else:
          ResolveParam(resolver)
        continue

      # Then try the registered defaults.
      unknown_field_exception = UnknownFieldException(
          self.__collectionpath, param)
      api_collection_funcs = self.__parser.registry.default_param_funcs.get(
          param)
      if not api_collection_funcs:
        raise unknown_field_exception
      api, collection = self.__collection.split('.')
      collection_funcs = api_collection_funcs.get(api)
      if not collection_funcs:
        raise unknown_field_exception
      if collection in collection_funcs:
        resolver = collection_funcs[collection]
      elif None in collection_funcs:
        resolver = collection_funcs[None]
      else:
        raise unknown_field_exception
      value = resolver() if callable(resolver) else resolver
      ResolveParam(value)

    self.__self_link = self.__parser.client.url + util.ExpandRelativePath(
        self.__parser.method_config, self.__dict__)

    if self.Collection().startswith('compute.'):
      # TODO(user): Unquote URLs for compute, pending b/15425944.
      self.__self_link = urllib.unquote(self.__self_link)

  def __str__(self):
    path = '/'.join([getattr(self, param) for param in self.__ordered_params])
    return '{collection}::{path}'.format(
        collection=self.__collection, path=path)


class Registry(object):
  """Keep a list of all the resource collections and their parsing functions.

  Attributes:
    parsers_by_collection: {str:_ResourceParser}, All the resource parsers
        indexed by their collection.
    parsers_by_url: Deeply-nested dict. The first key is the API's URL root,
        and each key after that is one of the remaining tokens which can be
        either a constant or a parameter name. At the end, a key of None
        indicates the value is a _ResourceParser.
    default_param_funcs: Triply-nested dict. The first key is the param name,
        the second is the api name, and the third is the collection name. The
        value is a function that can be called to find values for params that
        aren't specified already. If the collection key is None, it matches
        all collections.

  """

  def __init__(self):
    self.parsers_by_collection = {}
    self.parsers_by_url = {}
    self.default_param_funcs = {}

  def RegisterAPI(self, api, urls_only):
    """Register a generated API with this registry.

    Args:
      api: base_api.BaseApiClient, The client for a Google Cloud API.
      urls_only: bool, True if this API should only be used to interpret URLs,
          and not to interpret collectionpaths.
    """
    if api.url not in self.parsers_by_url:
      self.parsers_by_url[api.url] = {}

    for potential_service in api.__dict__.values():
      if not isinstance(potential_service, base_api.BaseApiService):
        continue
      try:
        parser = _ResourceParser(potential_service, self)

        if not urls_only:
          if parser.collection in self.parsers_by_collection:
            urls = [api.url,
                    self.parsers_by_collection[parser.collection].client.url]
            raise AmbiguousAPIException(parser.collection, urls)
          self.parsers_by_collection[parser.collection] = parser
        method_config = potential_service.GetMethodConfig('Get')
        tokens = method_config.relative_path.split('/')
        # Build up a search tree to match URLs against URL templates.
        # The tree will branch at each URL segment, where the first segment
        # is the API's base url, and each subsequent segment is a token in
        # the instance's get method's relative path. At the leaf, a key of
        # None indicates that the URL can finish here, and provides the parser
        # for this resource.
        cur_level = self.parsers_by_url[api.url]
        while tokens:
          token = tokens.pop(0)
          if token not in cur_level:
            cur_level[token] = {} if tokens else {None: parser}
          cur_level = cur_level[token]
      except _ResourceWithoutGetException:
        pass

  def SetParamDefault(self, api, collection, param, resolver):
    """Provide a function that will be used to fill in missing values.

    Args:
      api: str, The name of the API that func will apply to.
      collection: str, The name of the collection that func will apploy to. Can
          be None to indicate all collections within the API.
      param: str, The param that can be satisfied with func, if no value is
          provided by the path.
      resolver: str or func()->str, A function that returns a string or raises
          an exception that tells the user how to fix the problem, or the value
          itself.

    Raises:
      ValueError: If api or param is None.
    """
    if not api:
      raise ValueError('provided api cannot be None')
    if not param:
      raise ValueError('provided param cannot be None')
    if param not in self.default_param_funcs:
      self.default_param_funcs[param] = {}
    api_collection_funcs = self.default_param_funcs[param]
    if api not in api_collection_funcs:
      api_collection_funcs[api] = {}
    collection_funcs = api_collection_funcs[api]
    collection_funcs[collection] = resolver

  def ParseCollectionPath(self, collection, collectionpath, kwargs,
                          resolve=True):
    if collection not in self.parsers_by_collection:
      raise InvalidCollectionException(collection)
    return self.parsers_by_collection[collection].ParseCollectionPath(
        collectionpath, kwargs, resolve)

  def ParseURL(self, url, collection):
    """Parse a URL into a Resource.

    This method does not yet handle "api.google.com" in place of
    "www.googleapis.com/api/version".

    Searches self.parsers_by_url to find a _ResourceParser. The parsers_by_url
    attribute is a deeply nested dictionary, where each key corresponds to
    a URL segment. The first segment is an API's base URL (eg.
    "https://www.googleapis.com/compute/v1/"), and after that it's each
    remaining token in the URL, split on '/'. Then a path down the tree is
    followed, keyed by the extracted pieces of the provided URL. If the key in
    the tree is a literal string, like "project" in .../project/{project}/...,
    the token from the URL must match exactly. If it's a parameter, like
    "{project}", then any token can match it, and that token is stored in a
    dict of params to with the associated key ("project" in this case). If there
    are no URL tokens left, and one of the keys at the current level is None,
    the None points to a _ResourceParser that can turn the collected
    params into a Resource.

    Args:
      url: str, The URL of the resource.
      collection: str, The intended collection for the parsed resource, or None
          if unconstrained.

    Returns:
      Resource, The resource indicated by the provided URL.

    Raises:
      InvalidResourceException: If the provided URL could not be turned into
          a cloud resource.
      WrongResourceCollectionException: If the provided URL points into a
          collection other than the one specified.
    """
    match = _URL_RE.match(url)
    if not match:
      raise InvalidResourceException(url)
    base_url, path = match.groups()
    tokens = [base_url] + path.split('/')
    params = {}

    cur_level = self.parsers_by_url
    for token in tokens:
      if token in cur_level:
        # If the literal token is already here, follow it down.
        cur_level = cur_level[token]
      elif len(cur_level) == 1:
        # If the literal token is not here, and there is only one key, it must
        # be a parameter that will be added to the params dict.
        param = cur_level.keys()[0]
        if not param.startswith('{') or not param.endswith('}'):
          raise InvalidResourceException(url)
        # Clean up the provided value
        params[param[1:-1]] = urllib.unquote(token)
        # Keep digging down.
        cur_level = cur_level[param]
      else:
        # If the token we want isn't here, and there isn't a single parameter,
        # the URL we've been given doesn't match anything we know about.
        raise InvalidResourceException(url)
      # NB This will break if there are multiple parameters that could be
      # specified at a given level. As far as I can tell, this never happens and
      # never should happen. But in theory it's possible so we'll keep an eye
      # out for this issue.

    # No more tokens, so look for a parser.
    if None not in cur_level:
      raise InvalidResourceException(url)
    parser = cur_level[None]
    resource = parser.ParseCollectionPath(None, params, resolve=True)

    if collection and resource.Collection() != collection:
      raise WrongResourceCollectionException(
          expected=collection, got=resource.Collection())
    return resource

  def Parse(self, line, params=None, collection=None, resolve=True):
    """Parse a Cloud resource from a command line.

    Args:
      line: str, The argument provided on the command line.
      params: {str:str}, The keyword argument context.
      collection: str, The resource's collection, or None if it should be
        inferred from the line.
      resolve: bool, If True, call the resource's .Resolve() method before
          returning, ensuring that all of the resource parameters are defined.
          If False, don't call them, under the assumption that it will be called
          later.

    Returns:
      A resource object.

    Raises:
      InvalidResourceException: If the line is invalid.
      UnknownCollectionException: If no collection is provided or can be
          inferred.
      WrongProtocolException: If the input was http:// instead of https://
    """
    # Indirect default for kwargs.
    if not params:
      params = {}
    if line and line.startswith('https://'):
      return self.ParseURL(line, collection)
    elif line and line.startswith('http://'):
      raise WrongProtocolException()
    else:
      if not collection:
        match = _COLLECTIONPATH_RE.match(line)
        if not match:
          raise InvalidResourceException(line)
        collection, unused_path = match.groups()
      if not collection:
        raise UnknownCollectionException(line)

      return self.ParseCollectionPath(
          collection, line, params, resolve)


_REGISTRY = Registry()


def RegisterAPI(api, urls_only=False):
  """Register a generated API for parsing.

  Args:
    api: base_api.BaseApiClient, The client for a Google Cloud API.
    urls_only: bool, True if this API should only be used to interpret URLs,
        and not to interpret collectionpaths.
  """
  _REGISTRY.RegisterAPI(api, urls_only)


def SetParamDefault(api, collection, param, resolver):
  """Provide a function that will be used to fill in missing values.

  Args:
    api: str, The name of the API that func will apply to.
    collection: str, The name of the collection that func will apploy to. Can
        be None to indicate all collections within the API.
    param: str, The param that can be satisfied with func, if no value is
        provided by the path.
    resolver: str or func()->str, A function that returns a string or raises an
        exception that tells the user how to fix the problem, or the value
        itself.
  """
  _REGISTRY.SetParamDefault(api, collection, param, resolver)


def _ClearAPIs():
  """For testing, clear out any APIs to start with a clean slate.

  """
  global _REGISTRY
  _REGISTRY = Registry()


def Parse(line, params=None, collection=None, resolve=True):
  """Parse a Cloud resource from a command line.

  Args:
    line: str, The argument provided on the command line.
    params: {str:str}, The keyword argument context.
    collection: str, The resource's collection, or None if it should be
      inferred from the line.
    resolve: bool, If True, call the resource's .Resolve() method before
        returning, ensuring that all of the resource parameters are defined.
        If False, don't call them, under the assumption that it will be called
        later.

  Returns:
    A resource object.

  Raises:
    InvalidResourceException: If the line is invalid.
    UnknownCollectionException: If no collection is provided or can be inferred.
    WrongProtocolException: If the input was http:// instead of https://
  """
  return _REGISTRY.Parse(
      line=line, params=params, collection=collection, resolve=resolve)
