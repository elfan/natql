from constants import COLUMNS
from entity_engine import find_matching_entity_name_candidates, resolve_alternative_names
from plural_engine import get_plural_term
from util import get_normal_term

def get_is_match_table(query, table_name):
  table_schema = {
    table_name: {
      COLUMNS: {}
    }
  }
  resolve_alternative_names(table_schema)
  print('table_schema', table_schema[table_name]['names'])
  candidates = find_matching_entity_name_candidates(query, table_schema)
  print(query, table_name, candidates)
  return len(candidates) == 1 and candidates[0]['table'] == table_name

def get_is_match_column(query, column_name):
  table_schema = {
    'mytable': {
      COLUMNS: {
        column_name: {}
      }
    }
  }
  resolve_alternative_names(table_schema)
  print('table_schema', table_schema['mytable'][COLUMNS][column_name]['names'])
  candidates = find_matching_entity_name_candidates(query, table_schema)
  print(query, column_name, candidates)
  return len(candidates) == 1 and candidates[0][COLUMNS] == column_name

def test_find_matching_entity_name_candidates():
  name = 'Soccer_Stadium'
  names = {}
  names['original'] = name
  names['normal'] = get_normal_term(name)
  names['plural'] = get_plural_term(names['normal'])
  names['lower'] = name.lower()
  names['lower_normal'] = names['normal'].lower()
  names['lower_plural'] = names['plural'].lower()
  for query_attr in names:
    for name_attr in names:
      assert get_is_match_table(names[query_attr], names[name_attr])
      assert get_is_match_column(names[query_attr], names[name_attr])
