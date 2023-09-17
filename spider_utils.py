import json
import os
import re
import time

from matplotlib.pyplot import table
from constants import COLUMNS, DATA_TYPE, TYPE_INT, TYPE_TEXT
from natql_engine import NatQLEngine
from schema_utils.read_schema_sql import get_table_schemas_from_sql
from schema_utils.read_schema_sqlite import get_table_schemas_from_sqlite
from schema_utils.schema_utils import get_schema_signature
from util import file_get_json

spider_path = '../spider'

def load_test_db_files_from_spider(db_name = None):
  cache_file = 'cache/load_test_db_files_from_spider.json'
  if db_name is None and os.path.exists(cache_file):
    return file_get_json(cache_file)

  spider_db_path = spider_path + '/database'
  db_folders = [db_name] if db_name else os.listdir(spider_db_path)
  db_schemas = {}
  for db_folder in db_folders:
    db_path = spider_db_path + '/' + db_folder
    if not os.path.isdir(db_path):
      continue

    schema1 = None
    schema2 = None
    sql_files = os.listdir(db_path)
    for sql_file in sql_files:
      file_path = db_path + '/' + sql_file
      if re.search(r'\.sqlite$', sql_file):
        schema1 = get_table_schemas_from_sqlite(file_path)
      if re.search(r'\.sql$', sql_file):
        schema2 = get_table_schemas_from_sql(file_path)

    if schema1:
      schema1 = fix_inconsistencies_in_spider_data(db_folder, 'sqlite', schema1, schema2)
    if schema2:
      schema2 = fix_inconsistencies_in_spider_data(db_folder, 'sql', schema2, schema1)

    sig1 = get_schema_signature(schema1)
    sig2 = get_schema_signature(schema2)
    if schema1 and schema2 and (sig1 != sig2):
      print('Schema not the same', db_folder)
      print('sqllite', sig1, '\n')
      print('sqldump', sig2)
      return db_schemas
    elif schema1:
      db_schemas[db_folder] = schema1
    elif schema2:
      db_schemas[db_folder] = schema2
    else:
      print('Schema not recognized', db_folder)

  if not db_name:
    with open(cache_file, 'w', encoding='utf8') as f:
      f.write(json.dumps(db_schemas, indent=2))

  print('sqllite')
  print(sig1)
  print('sql')
  print(sig2)
  return db_schemas[db_name] if db_name else db_schemas

def fix_inconsistencies_in_spider_data(db_folder, file_type, table_schema, other_schema):
  if db_folder == 'formula_1' and file_type == 'sqlite':
    table_schema['circuits'][COLUMNS]['alt'][DATA_TYPE] = TYPE_INT
    table_schema['results'][COLUMNS]['fastestLap'][DATA_TYPE] = TYPE_INT
    table_schema['results'][COLUMNS]['laps'][DATA_TYPE] = TYPE_INT
    table_schema['results'][COLUMNS]['milliseconds'][DATA_TYPE] = TYPE_INT
    table_schema['results'][COLUMNS]['position'][DATA_TYPE] = TYPE_INT
    table_schema['results'][COLUMNS]['rank'][DATA_TYPE] = TYPE_INT

  if db_folder == 'formula_1' and file_type == 'sql':
    table_schema['constructorResults'][COLUMNS]['status'][DATA_TYPE] = TYPE_TEXT
    table_schema['drivers'][COLUMNS]['number'][DATA_TYPE] = TYPE_TEXT

  if db_folder == 'soccer_1' and file_type == 'sqlite':
    return other_schema

  if db_folder == 'wta_1' and file_type == 'sqlite':
    return other_schema

  return table_schema

def load_test_question_files_from_spider():
  spider_json_files = [
    'dev.json', # 1034 questions / 20 databases
    'train_spider.json', # 7000 questions / 140 databases
    'train_others.json', # 1659 questions / 6 databases
  ]

  challenges = []
  for json_file in spider_json_files:
    json_data = file_get_json(spider_path + '/' + json_file)
    for entry in json_data:
      fix_inconrrectness_in_spider_data(entry)
      challenges.append({
        'question': entry.get('question'),
        'query': entry.get('query'),
        'db_id': entry.get('db_id'),
      })

  return challenges

def fix_inconrrectness_in_spider_data(entry):
  # there is an error in the train_spider.json file
  if entry.get('db_id') == 'soccer_1' and entry.get('question') == 'What is the maximum and minimum height of all players?':
    entry['question'] = 'What is the maximum and minimum weight of all players?'
  if entry.get('db_id') == 'battle_death' and entry.get('question') == 'List the name, date and result of each battle.':
    entry['query'] = 'SELECT name ,  date, result FROM battle'

def normalize_sql_query(sql):
  """
  make sure it is one line
  make sure all spaces are one space
  trim
  remove space before comma and near parentheses
  remove ticks
  remove semi colon
  lowercase
  """
  sql = re.sub(r';', '', sql)      # remove semi colon
  sql = re.sub(r'[()]', ' ', sql)  # remove parentheses
  sql = re.sub(r'\s+', ' ', sql)   # make sure there is no newline and multiple spaces
  sql = re.sub(r' ?, ?', ',', sql) # remove space before and after comma
  sql = sql.strip()                # trim spaces
  sql = re.sub(r'`', '', sql)      # remove ticks
  sql = re.sub(r'"', "'", sql)     # replace double with single quotes
  sql = re.sub(r'\bASC\b', '', sql, re.IGNORECASE)      # remove optional ASC
  sql = sql.lower().strip()
  if match := re.search(r'^select (.+) from', sql):
    columns = re.split(',', match.group(1))
    columns.sort()
    sql = re.sub(r'^select (.+) from', 'select ' + ','.join(columns) + ' from', sql)
  return sql

if __name__ == '__main__':
  start = time.time()
  db_schemas = load_test_db_files_from_spider()
  challenges = load_test_question_files_from_spider()

  success_only = 0

  success_file = 'cache/success_cases.json'
  prev_success_cases = file_get_json(success_file) if os.path.exists(success_file) else {}
  print(prev_success_cases)

  success_cases = {}
  success_count = 0
  broken_count = 0
  uncaught_count = 0
  i = 0
  agent = NatQLEngine(debug = False)
  for challenge in challenges:
    i += 1
    if success_only and not prev_success_cases.get(i): continue
    agent.set_table_schemas(db_schemas[challenge['db_id']])
    result = agent.get_answer(challenge['question'])
    db_id = challenge['db_id']
    question = challenge['question']
    query = challenge['query']
    n_query = normalize_sql_query(query)
    result_query = result['sql_query']
    n_result_query = normalize_sql_query(result_query)
    result_parts = result['parts']

    if i % 100 == 0:
      print('-------', i)

    if n_result_query == n_query:
      success_count += 1
      success_cases[i] = {'db': db_id, 'question': question, 'query': result_query}
      print(success_count, i)
    else:
      if prev_success_cases.get(i):
        # previously success but now broken
        broken_count += 1
        print('===', 'BROKEN', i, db_id)
        print(prev_success_cases[i]['db'])
        print(prev_success_cases[i]['question'])
        print(prev_success_cases[i]['query'])
        print(result_query, "\n")

      if 0 and not re.search(r'(having|group|t\d+|limit|\(select)', n_query):
        uncaught_count += 1
        print('===', 'NO', db_id)
        print(question)
        print(n_query)
        print(n_result_query, "\n")
      elif re.search(r'join', n_query) and abs(len(n_query) - len(n_result_query)) < 100:
        uncaught_count += 1
        print('===', 'NO', db_id)
        print(question)
        print(result_parts)
        print(n_query)
        print(n_result_query, "\n")

  if broken_count == 0 and success_cases:
    with open(success_file, 'w', encoding='utf8') as f:
      f.write(json.dumps(success_cases, indent=2))
  
  print('broken', broken_count)
  print('success', success_count, '/', i, success_count/i*100, '%')
  print(time.time() - start, 'seconds')
  print('uncaught', uncaught_count, '/', (uncaught_count + success_count))

  print(len(db_schema), 'databases loaded')
