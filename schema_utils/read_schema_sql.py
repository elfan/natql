import re

from constants import COLUMNS, DATA_TYPE, FOREIGN_KEY, PRIMARY_KEY
from schema_utils.schema_utils import get_normalized_data_type, re_column_type


def get_table_schemas_from_sql(sql_file):
  f = open(sql_file, 'r', encoding='utf8')
  lines = f.readlines()
  f.close()

  # normalize
  lines = re.sub(r'\/\*.*?\*\/', '', ''.join(lines), flags=re.DOTALL).strip()
  lines = re.sub(r'--.*?\n', '\n', lines, flags=re.MULTILINE)
  lines = lines.split(';')
  lines = list(map(lambda x: re.sub(r'\s+', ' ', x).strip(), lines))

  # parsing
  patt_column_chars = r'[\w%]' # without space, which will be added separately
  patt_extra_column_chars_with_quotes = r'[ ()]'
  patt_entity = r'(?:["\'`\[](?:' + patt_column_chars + '|' + patt_extra_column_chars_with_quotes + ')+["\'`\]]|' + patt_column_chars + '+)'
  patt_entity_list = r'(?:' + patt_entity + '(?: ?, ?' + patt_entity + ')*)'
  patt_type = r'(?:' + '|'.join(map(lambda x: re_column_type[x].pattern, re_column_type.keys())) + ')'
  patt_constraint = r'CONSTRAINT \w+'
  re_primary = re.compile(r'(?:' + patt_constraint + ' )?PRIMARY KEY ?\( ?(.*?) ?\)', re.IGNORECASE)
  re_foreign = re.compile(r'(?:' + patt_constraint + ' )?FOREIGN KEY ?\( ?(' + patt_entity_list + ') ?\) references (' + patt_entity + ') ?\( ?(' + patt_entity_list + ') ?\)(?: (?:on|delete|update)[\w ]+)?', re.IGNORECASE)
  patt_check_exp = r'(?:[^()]+(?:\([^())]*\))?)*'
  patt_extra_info = r'(?:NOT NULL|NULL|UNIQUE|PRIMARY KEY|AUTOINCREMENT|DEFAULT (?:NULL|TRUE|FALSE|CURRENT_TIMESTAMP|\d+(?:\.\d+)?|\'[^\']*\')|CHECK ?\(' + patt_check_exp + '\))'
  re_entity_and_type = re.compile(r'(' + patt_entity + ') (' + patt_type + ')((?: ' + patt_extra_info + ')*)', re.IGNORECASE)
  re_entity_without_type = re.compile(r'((?!(?:PRIMARY KEY|FOREIGN KEY))' + patt_entity + ')()((?: ' + patt_extra_info + ')+)', re.IGNORECASE)
  re_ignored_column_def = re.compile(r'^(?:UNIQUE ?\((.*?)\))')
  re_column_def = re.compile('^\s*(' + re_primary.pattern + '|' + re_foreign.pattern + '|' + re_ignored_column_def.pattern + '|' + re_entity_and_type.pattern + '|' + re_entity_without_type.pattern + ')', re.IGNORECASE)
  re_create_table = re.compile(r'^CREATE TABLE(?: IF NOT EXISTS)? (' + patt_entity + ')', re.IGNORECASE)
  table_schemas = {}
  for line in lines:
    if match := re_create_table.search(line):
      ori_line = line
      line = re_create_table.sub('', line)
      line = re.sub(r'^ ?\( ?', '', line) # remove opening parentheses of column_def
      table_name = remove_quotes(match.group(1))
      schema = {COLUMNS: {}, PRIMARY_KEY: []}
      while line and (match := re_column_def.search(line)):
        line = re_column_def.sub('', line)
        line = re.sub(r'^ ?, ?', '', line) # remove separator between column_defs
        column_def = match.group(1)
        if match := re_primary.search(column_def):
          key_list = re.split(r' ?, ?', match.group(1).strip())
          key_list = list(map(remove_quotes, key_list))
          schema[PRIMARY_KEY] = key_list
        elif match := re_foreign.search(column_def):
          key_name = remove_quotes(match.group(1))
          ref_table = remove_quotes(match.group(2))
          ref_column = remove_quotes(match.group(3))
          if not schema.get(FOREIGN_KEY): schema[FOREIGN_KEY] = {} # init
          schema[FOREIGN_KEY][key_name] = {'table': ref_table, 'column': ref_column}
        elif (match := re_entity_and_type.search(column_def)) or (match := re_entity_without_type.search(column_def)):
          column_name = remove_quotes(match.group(1))
          column_type = match.group(2)
          is_primary = None
          is_nullable = None
          default_val = None
          is_auto_increment = None
          if match.group(3):
            is_primary = re.search(r'PRIMARY KEY', match.group(3), re.IGNORECASE)
            if is_primary:
              schema[PRIMARY_KEY].append(column_name)
            if m := re.search(r'(NOT NULL|NULL)', match.group(3), re.IGNORECASE):
              is_nullable = not re.search(r'NOT', m.group(1), re.IGNORECASE)
            if m := re.search(r'DEFAULT (NULL|\'([^\']*)\')', match.group(3), re.IGNORECASE):
              if m.group(1).upper() == 'NULL':
                default_val = 'NULL'
              elif m.group(1).upper() == 'TRUE':
                default_val = True
              elif m.group(1).upper() == 'FALSE':
                default_val = False
              elif m.group(1).upper() == 'CURRENT_TIMESTAMP':
                default_val = 'CURRENT_TIMESTAMP'
              elif m.group(1):
                default_val = m.group(1)
              else:
                default_val = m.group(2)
            if m := re.search(r'AUTOINCREMENT', match.group(3), re.IGNORECASE):
              is_auto_increment = True
          data_type = get_normalized_data_type(column_type)
          schema[COLUMNS][column_name] = {'type': column_type, DATA_TYPE: data_type}
          if is_nullable is not None:
            schema[COLUMNS][column_name]['nullable'] = is_nullable
          if is_auto_increment is not None:
            schema[COLUMNS][column_name]['auto_inc'] = is_auto_increment
          if default_val is not None:
            schema[COLUMNS][column_name]['default'] = None if default_val == 'NULL' else default_val

      line = re.sub(r'^ ?\) ?', '', line) # remove closing parentheses of column_def
      if not re.search(r'^\s*$', line):
        print('Warning: unrecognized remaining string in ' + sql_file + ':', line)
        print('Complete string:', ori_line)

      table_schemas[table_name] = schema
  return table_schemas

def remove_quotes(entity_name):
  return re.sub(r'["\'`\[\]]', '', entity_name).strip()