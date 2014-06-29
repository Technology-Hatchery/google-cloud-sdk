# Copyright 2014 Google Inc. All Rights Reserved.
"""Facilities for printing Python objects."""
import collections
import cStringIO
import json
import os
import sys


import yaml


_INDENTATION = 2


class ResourcePrinter(object):
  """Base class for printing Python objects."""

  def __init__(self, out=None):
    self._out = out or sys.stdout

  def PrintHeader(self):
    """Prints a header if the output format requires one."""

  def AddRecord(self, record):
    """Adds a record for printing.

    Formats that can be outputted in a streaming manner (e.g., YAML)
    can print their results every time AddRecord() is called. Formats
    that cannot be outputted in a streaming manner (e.g., JSON) should
    not print anything when this method is called and should instead
    print their results when Finish() is called.

    Args:
      record: A record to print. This can be any Python object that can
        be serialized to the format that the subclass requires.
    """

  def Finish(self):
    """Prints the results for formats that cannot stream their output."""


class JsonPrinter(ResourcePrinter):
  """Prints all records as a JSON list."""

  def __init__(self, *args, **kwargs):
    """Creates a new JsonPrinter."""
    super(JsonPrinter, self).__init__(*args, **kwargs)
    self._records = []

  def AddRecord(self, record):
    """Adds a JSON-serializable Python object to the list.

    Because JSON output cannot be streamed, this method does not
    actually print anything.

    Args:
      record: A JSON-serializable Python object.
    """
    self._records.append(record)

  def Finish(self):
    """Prints the JSON list to the output stream."""
    json.dump(
        self._records,
        fp=self._out,
        indent=_INDENTATION,
        sort_keys=True,
        separators=(',', ': '))
    self._out.write('\n')


class YamlPrinter(ResourcePrinter):
  """A printer that outputs YAML representations of YAML-serializable objects.

  For example:

    printer = YamlPrinter(sys.stdout)
    printer.AddRecord({'a': ['hello', 'world'], 'b': {'x': 'bye'}})

  produces:

    ---
    a:
      - hello
      - world
    b:
      - x: bye
  """

  def AddRecord(self, record):
    """Immediately prints the given record as YAML.

    A "---" is printed before the actual record to delimit the
    document.

    Args:
      record: A YAML-serializable Python object.
    """
    yaml.add_representer(
        collections.OrderedDict,
        yaml.dumper.SafeRepresenter.represent_dict,
        Dumper=yaml.dumper.SafeDumper)
    yaml.safe_dump(
        record,
        stream=self._out,
        default_flow_style=False,
        indent=_INDENTATION,
        explicit_start=True)


def _Flatten(obj):
  """Flattens a JSON-serializable object into a list of tuples.

  The first element of each tuple will be a key and the second element
  will be a simple value.

  For example, _Flatten({'a': ['hello', 'world'], 'b': {'x': 'bye'}})
  will produce:

    [
        ('a[0]', 'hello'),
        ('a[1]', 'world'),
        ('b.x', 'bye'),
    ]

  Args:
    obj: A JSON-serializable object.

  Returns:
    A list of tuples.
  """

  class Index(str):
    pass

  class Key(str):
    pass

  def IntegerLen(integer):
    return len(str(integer))

  def ConstructFlattenedKey(path):
    """[Key('a'), Index('1'), Key('b')] -> 'a[1].b'."""
    buf = cStringIO.StringIO()
    for i in xrange(len(path)):
      if isinstance(path[i], Index):
        buf.write('[')
        buf.write(str(path[i]))
        buf.write(']')
      else:
        if i > 0:
          buf.write('.')
        buf.write(str(path[i]))
    return buf.getvalue()

  def Flatten(obj, path, res):
    if isinstance(obj, list):
      for i in xrange(len(obj)):
        zfilled_idx = str(i).zfill(IntegerLen(len(obj) - 1))
        Flatten(obj[i], path + [Index(zfilled_idx)], res)
    elif isinstance(obj, dict):
      for key, value in obj.iteritems():
        Flatten(value, path + [Key(key)], res)
    else:
      res[ConstructFlattenedKey(path)] = obj

  res = collections.OrderedDict()
  Flatten(obj, [], res)
  return res


class DetailPrinter(ResourcePrinter):
  """A printer that can flatten JSON representations of objects.

  For example:

    printer = DetailPrinter(sys.stdout)
    printer.AddRecord({'a': ['hello', 'world'], 'b': {'x': 'bye'}})

  produces:

    ---
    a[0]: hello
    a[1]: world
    b.x:  bye
  """

  def AddRecord(self, record):
    """Immediately prints the record as a flattened JSON object.

    A "document delimiter" of "---" is inserted before the object.

    Args:
      record: A JSON-serializable object.
    """
    self._out.write('---\n')
    flattened_record = sorted(_Flatten(record).items())
    max_key_len = max(len(key) for key, _ in flattened_record)

    for key, value in flattened_record:
      self._out.write(key + ':')
      self._out.write(' ' * (max_key_len - len(key)))
      self._out.write(' ')
      self._out.write(str(value))
      self._out.write('\n')


def _Stringify(value):
  """Dumps value to JSON if it's not a string."""
  if not value:
    return ''
  elif isinstance(value, basestring):
    return value
  else:
    return json.dumps(value, sort_keys=True)


class TablePrinter(ResourcePrinter):
  """A printer for printing human-readable tables."""

  def __init__(self, *args, **kwargs):
    """Creates a new TablePrinter."""
    super(TablePrinter, self).__init__(*args, **kwargs)
    self._rows = []

  def AddRow(self, row):
    """Adds a record without outputting anything."""
    self._rows.append(row)

  def Print(self):
    """Prints the actual table."""
    if not self._rows:
      self._out.write(os.linesep)
      return

    rows = [[_Stringify(cell) for cell in row] for row in self._rows]
    col_widths = [0] * len(rows[0])
    for row in rows:
      for i in xrange(len(row)):
        col_widths[i] = max(col_widths[i], len(row[i]))

    for row in rows:
      line = cStringIO.StringIO()
      for i in xrange(len(row) - 1):
        line.write(row[i].ljust(col_widths[i]))
        line.write(' ')
      if row:
        line.write(row[len(row) - 1])
      self._out.write(line.getvalue().strip())
      self._out.write(os.linesep)


_FORMATTERS = {
    'json': JsonPrinter,
    'yaml': YamlPrinter,
    'text': DetailPrinter,
}

SUPPORTED_FORMATS = sorted(_FORMATTERS)


def Print(resources, print_format, out=None):
  """Prints the given resources.

  Args:
    resources: A list of JSON-serializable Python dicts.
    print_format: One of json, yaml, or text.
    out: A file-like object for writing results to.

  Raises:
    ValueError: If print_format is invalid.
  """

  formatter_class = _FORMATTERS.get(print_format)
  if not formatter_class:
    raise ValueError('formats must be one of {0}; received {1}'.format(
        ', '.join(SUPPORTED_FORMATS), print_format))

  formatter = formatter_class(out=out)
  formatter.PrintHeader()

  # resources may be a generator and since generators can raise
  # exceptions, we have to call Finish() in the finally block to make
  # sure that the resources we've been able to pull out of the
  # generator are printed before control is given to the
  # exception-handling code.
  try:
    for resource in resources:
      formatter.AddRecord(resource)
  finally:
    formatter.Finish()
