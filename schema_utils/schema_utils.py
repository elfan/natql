import json
import re
from constants import COLUMNS, DATA_TYPE, FOREIGN_KEY, PRIMARY_KEY, TYPE_BLOB, TYPE_BOOL, TYPE_INT, TYPE_TEXT, TYPE_TIME

re_column_type = {
  TYPE_INT: re.compile(r'(?:(?:unsigned|signed) )?(?:integer|int|tinyint|smallint|mediumint|bigint|bit|decimal|numeric|number|float|real|double)(?: ?\(\d+(?: ?, ?\d+)?\))?(?: (?:unsigned|signed))?', re.IGNORECASE),
  TYPE_BOOL: re.compile(r'(?:boolean|bool|binary)', re.IGNORECASE),
  TYPE_TIME: re.compile(r'(?:datetime|timestamp|date|time|year)', re.IGNORECASE),
  TYPE_TEXT: re.compile(r'(?:text|char|varchar2?|text)(?: ?\(\d+\))?', re.IGNORECASE),
  TYPE_BLOB: re.compile(r'(?:blob)', re.IGNORECASE),
}

def is_equal_table_schema(table_schema1, table_schema2, with_foreign_key = False):
  return get_schema_signature(table_schema1, with_foreign_key) == get_schema_signature(table_schema2, with_foreign_key)

def get_schema_signature(table_schema, with_foreign_key = False):
  return json.dumps(get_core_table_schema(table_schema, with_foreign_key)).lower()

def get_core_table_schema(table_schema, with_foreign_key = False):
  core_schema = {}
  if not table_schema:
    return core_schema

  table_map = {}
  for table_name in table_schema:
    table_map[table_name.lower()] = table_name

  for table_lower in sorted(table_map.keys()):
    table_name = table_map[table_lower]
    table = table_schema[table_name]

    column_map = {}
    for column_name in table[COLUMNS]:
      column_map[column_name.lower()] = column_name

    schema = {COLUMNS: {}, PRIMARY_KEY: table[PRIMARY_KEY]}
    for column_lower in sorted(column_map.keys()):
      column_name = column_map[column_lower]
      column = table[COLUMNS][column_name]
      schema[COLUMNS][column_name] = column[DATA_TYPE]

    if with_foreign_key and table.get(FOREIGN_KEY):
      schema[FOREIGN_KEY] = {}
      for key in table[FOREIGN_KEY]:
        ref = table[FOREIGN_KEY][key]
        schema[FOREIGN_KEY][key] = {'table': ref['table'], 'column': ref['column']}

    core_schema[table_name] = schema
  return core_schema


def get_normalized_data_type(column_type):
  for type in re_column_type:
    if re_column_type[type].search(column_type):
      return type
  return ''
