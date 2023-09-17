import json
import re
from constants import COLUMNS, DATA_TYPE, FOREIGN_KEY, HAVING, KIND, PRIMARY_KEY
from plural_engine import get_plural_term
from schema_utils.schema_utils import get_normalized_data_type
from util import get_normal_term


def resolve_column_data_types(table_schemas):
  for table_name in table_schemas:
    table_schema = table_schemas[table_name]
    column_schemas = table_schema[COLUMNS]
    for column_name in column_schemas:
      if not column_schemas[column_name].get(DATA_TYPE):
        column_schemas[column_name][DATA_TYPE] = get_normalized_data_type(column_schemas[column_name]['type'])

def resolve_primary_keys(table_schemas):
  # primary keys are usually already defined in the CREATE script, but if it isn't, find if there is any
  for table_name in table_schemas:
    table_schema = table_schemas[table_name]
    if table_schema.get(PRIMARY_KEY): continue
    # no primary key info from the CREATE script
    table_schema[PRIMARY_KEY] = []   # init
    # let's guess
    if table_schema[HAVING].get('id'):
      table_schema[PRIMARY_KEY].append(table_schema[HAVING]['id']['column'])


def resolve_foreign_keys(table_schemas):
  for table_name in table_schemas:
    table_schema = table_schemas[table_name]
    if table_schema.get(FOREIGN_KEY): continue
    # no foreign key info from the CREATE script
    foreign_keys = {}
    column_schemas = table_schema[COLUMNS]
    for column_name in column_schemas:
      prefix = get_prefix_name_having_concept(column_name, 'id')
      if prefix:
        for other_table in table_schemas:
          if other_table == table_name: continue
          if is_text_part_of_name(prefix, other_table) and table_schemas[other_table][HAVING].get('id'):
            foreign_keys[column_name] = {'column': table_schemas[other_table][HAVING]['id']['column'], 'table': other_table}
    if foreign_keys:
      table_schema[FOREIGN_KEY] = foreign_keys

def add_obj_alternative_names(obj, name):
  """
  obj could be a table or column object
  this will modify the obj by adding 'name' and 'alias' (if necessary)
  - original e.g. "Stadium_ID"
  - normal e.g. "Stadium ID"
  - plural e.g. "Stadium IDs"
  - lower e.g. "stadium_id"
  - lower_normal e.g. "stadium id"
  - lower_plural e.g. "stadium ids"
  """
  names = {'original': name}

  lower_name = name.lower()
  if lower_name != name:
    names['lower'] = lower_name

  normal_name = get_normal_term(name)
  if normal_name != name:
    names['normal'] = normal_name
    lower_normal = normal_name.lower()
    if lower_normal != normal_name:
      names['lower_normal'] = lower_normal

  plural_name = get_plural_term(normal_name)
  if plural_name != normal_name:
    names['plural'] = plural_name
    lower_plural = plural_name.lower()
    if lower_plural != plural_name:
      names['lower_plural'] = lower_plural
  
  obj['names'] = names


def resolve_alternative_names(table_schemas):
  """
  add name and alias names for all tables and column names
  """
  for table_name in table_schemas:
    add_obj_alternative_names(table_schemas[table_name], table_name)

    columns = table_schemas[table_name][COLUMNS]
    for column_name in columns:
      add_obj_alternative_names(columns[column_name], column_name)


def match_names(name, names, attr):
  attrs = [attr]
  if attr != 'original': # fallback path to original
    parts = attr.split('_')
    if len(parts) == 2:
      attrs.append(parts[1])
      attrs.append(parts[0])
    attrs.append('original')

  for a in attrs:
    if names.get(a) == name:
      return True


def find_table_name(name, table_schema, attr):
  for table_name in table_schema:
    table = table_schema[table_name]

    if match_names(name, table['names'], attr):
      return {'table': table_name, 'attr': attr}


def find_column_names(name, table_schemas, attr, non_unique=False):
  results = []
  unique_results = []
  for table_name in table_schemas:
    table = table_schemas[table_name]
    columns = table[COLUMNS]
    for column_name in columns:
      if match_names(name, columns[column_name]['names'], attr):
        item = {'table': table_name, 'column': column_name, 'attr': attr}
        if non_unique and (column_name in table[PRIMARY_KEY]):
          # asking a non unique but found a primary key, keep it as a fallback
          unique_results.append(item)
        else:
          results.append(item)

  return results if results else unique_results


def find_matching_entity_name_candidates(entity_name, table_schemas, priorities=[], non_unique=False):
  """
  normalize singular and plural when matching
  find one or more candidates based on the following priority
  - exact table name matching
  - exact column name matching
  - normal table name matching
  - normal column name matching
  - plural table name matching
  - plural column name matching
  repeat those for lowercase matching
  repeat those for partial matching
  return a list of candidates of {table, column}
  """
  candidates = []
  entity = {}
  entity['original'] = re.sub(r'`', r'', entity_name)
  entity['lower'] = entity['original'].lower()
  entity['normal'] = get_normal_term(entity['original'])
  entity['plural'] = get_plural_term(entity['normal'])
  entity['lower_normal'] = entity['normal'].lower()
  entity['lower_plural'] = entity['plural'].lower()

  exists = {}
  for attr in entity:
    # table name matching
    result = find_table_name(entity[attr], table_schemas, attr)
    if result:
      hash = result.get('table') + '.' + result.get('column', '')
      if not exists.get(hash):
        exists[hash] = True
        candidates.append(result)

    # column name matching
    results = find_column_names(entity[attr], table_schemas, attr, non_unique)
    for result in results:
      hash = result.get('table') + '.' + result.get('column', '')
      if not exists.get(hash):
        exists[hash] = True
        candidates.append(result)
  #print('cccc', entity_name, priorities, candidates)
  if ((priorities is not None) and
     (len(priorities) > 0) and
     ((len(candidates) == 1) or (len(candidates) > 1) and (priorities[0] != entity_name) and (not candidates[0].get('column')))):

    table_name = candidates[0].get('table')
    table_schema = table_schemas[table_name]
    sub_table_schema = {
      table_name: table_schema,
    }
    for col in priorities:
      if col == entity_name:
        continue
      sub_candidates = try_find_matching_in_sub_table_schema(col, sub_table_schema)
      if sub_candidates:
        return sub_candidates
      
  return candidates

def try_find_matching_in_sub_table_schema(col, sub_table_schema):
  sub_candidates = find_matching_entity_name_candidates(col, sub_table_schema)
  if len(sub_candidates) == 1:
    return sub_candidates
  if len(sub_candidates) == 0:
    table_schema = list(sub_table_schema.values())[0]
    if table_schema[HAVING].get(col):
      return [ table_schema[HAVING].get(col) ]

    # try to make col singular
    new_col = re.sub(r's$', r'', re.sub(r'ies$', r'y', col))
    if table_schema[HAVING].get(new_col):
      return [ table_schema[HAVING].get(new_col) ]

    # try to remove some words, e.g.
    # "phone numbers" -> "phone"
    # "email address" -> "email"
    # "cell count" -> "cell"
    # "profit value" -> "profit"
    # "snatch score" -> "snatch"
    # "committee information" -> "committee"
    # "student name" -> "student"
    # "bonus given" -> "bonus"
    # "the investors" -> "investors"
    new_col = re.sub(r'[ _](numbers?|address(es)?|counts?|values?|scores?|informations?|names?|given)$', r'', col)
    new_col = re.sub(r'^the[ _]', r'', new_col)
    if new_col and new_col != col:
      sub_candidates = try_find_matching_in_sub_table_schema(new_col, sub_table_schema)
      if sub_candidates: return sub_candidates

    # try to get something inside parentheses, e.g. "Online Mendelian Inheritance in An (OMIM) value" -> "OMIM"
    new_col = re.sub(r'^.+[(]([^()]+)[)].*$', r'\1', col)
    if new_col and new_col != col:
      sub_candidates = try_find_matching_in_sub_table_schema(new_col, sub_table_schema)
      if sub_candidates: return sub_candidates

def resolve_entity_kind(table_schemas):
  # kind is defining the concepts that the table has
  # is it about a person (who usually can have name, age, etc)? a thing (who don't)? relation table? etc
  for table_name in table_schemas:
    candidate_kinds = {}
    if entity_name := detect_person(table_name):
      candidate_kinds['person'] = {'entity': entity_name, 'table': table_name}

    table_schema = table_schemas[table_name]
    if len(table_schema[PRIMARY_KEY]) == 1:
      if entity_name := detect_person(table_schema[PRIMARY_KEY][0]):
        candidate_kinds['person'] = {'entity': entity_name, 'table': table_name, 'column': table_schema[PRIMARY_KEY][0]}

    table_schema[KIND] = {}
    if len(candidate_kinds) == 1:
      table_schema[KIND] = candidate_kinds
    elif len(candidate_kinds) == 0:
      if is_primary_equal_foreign_keys(table_schema):
        table_schema[KIND]['relation'] = {'size': len(table_schema[PRIMARY_KEY])}
      else:
        table_schema[KIND]['thing'] = {'entity': table_name, 'table': table_name}


def resolve_entity_having(table_schemas):
  # does it have column indicating id, location, age, temporal, etc
  concepts = [
    'id',
    'name',
    'type',
    'category',
    'weight',
    'height',
    'age',
    'birthday=birth[ _]?(day|date)', # can be followed by "=" and regex pattern that starts with a letter (not regex symbols like parentheses or ^)
    'birthday=dob',
  ]
  for table_name in table_schemas:
    having = {}
    table_schema = table_schemas[table_name]
    column_schemas = table_schema[COLUMNS]
    for column_name in column_schemas:
      for concept in concepts:
        if is_column_name_having_concept(column_name, concept, table_name):
          pair = concept.split('=', 2)
          concept_name = pair[0]
          having[concept_name] = {'column': column_name, 'table': table_name}
          if column_name in table_schema.get(PRIMARY_KEY, []):
            having[concept_name]['primary'] = True
    table_schema[HAVING] = having


def is_column_name_having_concept(column_name, concept, table_name = ''):
  prefix = get_prefix_name_having_concept(column_name, concept)
  if prefix == '':
    # no prefix means the concept is exact match with the column name, e.g. ID
    return True
  if prefix and is_text_part_of_name(prefix, table_name):
    # the prefix indicates table name, e.g. table Student has ID by having column StuID
    return True
  return False


def get_prefix_name_having_concept(column_name, concept):
  # e.g. if concept = "id", find if column name is ID, id, Id, StuID, StuId, stuId, Stu_ID, stu_id

  pair = concept.split('=', 2)
  pattern = pair[1] if len(pair) > 1 else pair[0]

  if match := re.search(r'^' + pattern + r'$', column_name, re.IGNORECASE):  # e.g. ID, id, Id
    # column_name matches concept name
    return ''

  if match := re.search(r'^(.*[^A-Z]|[A-Z])' + pattern[0:1].upper() + r'(?i:' + pattern[1:] + r')$', column_name):  # e.g. StuID, StuId, SID, stuId, but not STUID
    # column_name in camelCase has concept name as suffix
    return match.group(1)

  if match := re.search(r'^(.+)_' + pattern + r'$', column_name, re.IGNORECASE):  # e.g. Stu_ID, stu_id
    # column_name in snake_case has concept name as suffix
    return match.group(1)

  if len(pattern) >= 4 and (match := re.search(r'^(.+)' + pattern + r'$', column_name, re.IGNORECASE)):  # e.g. pettype
    # column_name without separator matches concept name
    return match.group(1)


def is_text_part_of_name(text, name):
  name = name.lower()
  text = text.lower()
  if name.find(text) == 0:
    return True
  if name.find(get_plural_term(text)) == 0:
    return True
  return False

def is_primary_equal_foreign_keys(table_schema):
  if len(table_schema[PRIMARY_KEY]) == 0:
    return False

  for key in table_schema[PRIMARY_KEY]:
    if not table_schema.get(FOREIGN_KEY, {}).get(key):
      return False
  return True

def detect_person(entity_name):
  name = entity_name
  name = re.sub(r'([a-z])I[Dd]\b', '\1', name)
  name = re.sub(r'_id\b', '', name.lower())
  name = name.lower()

  known_list = [ # must be singluar
    'person',
    'employee',
    'singer',
    'artist',
    'student',
  ]
  if name in known_list:
    return name

  plural_list = map(get_plural_term, known_list)
  if name in plural_list:
    return name

  return ''
