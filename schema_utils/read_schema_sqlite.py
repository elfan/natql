import re
import sqlite3

from constants import COLUMNS, DATA_TYPE, PRIMARY_KEY
from schema_utils.schema_utils import get_normalized_data_type


def get_table_schemas_from_sqlite(sqlite_file):
  conn = sqlite3.connect(sqlite_file)
  cursor = conn.cursor()
  result = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
  table_names = list(zip(*result))[0]

  table_schemas = {}
  for table_name in table_names:
    schema = {COLUMNS: {}, PRIMARY_KEY: []}
    result = cursor.execute("PRAGMA table_info('%s')" % table_name).fetchall()
    primary_keys = {}
    for row in result:
      idx, column_name, column_type, nullable, default_val, pk_idx = row
      schema[COLUMNS][column_name] = {
        'type': column_type,
        DATA_TYPE: get_normalized_data_type(column_type),
        'nullable': bool(nullable),
        'default': default_val,
      }
      if pk_idx > 0:
        primary_keys[pk_idx] = column_name

    for i in sorted(primary_keys):
      schema[PRIMARY_KEY].append(primary_keys[i])

    if table_name == 'sqlite_sequence':
      # most likely error
      pass
    else:
      table_schemas[table_name] = schema

  return table_schemas
