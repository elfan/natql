
from natql_engine import NatQLEngine
from util import file_get_json

def test_how_many():
  table_schema = file_get_json('tests/schema.json')
  agent = NatQLEngine(table_schema)

  queries = {}
  queries['SELECT COUNT(*) FROM `singer`'] = [
    "How many singers do we have?",
    "Could you tell me how many singers are there?",
    "What is the total number of singers",
    "What is the count of singers?",
    "Show me how many singers are there",
    "select count of singers",
    "SELECT COUNT(*) FROM `singers`",
    "total singers",
    "would you count the singers?",
    "count the singers, please?",
    "I want to know how many singers there are",
  ]

  for sql in queries:
    for text in queries[sql]:
      result = agent.find_answer(text)
      if result['sql_query'] != sql:
        print(text, result)
      assert result['sql_query'] == sql
