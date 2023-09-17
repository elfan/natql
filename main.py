import json
from natql_engine import NatQLEngine
from spider_utils import load_test_db_files_from_spider

#question = "Show name, country, age for all singers ordered by age from the oldest to the youngest."
#question = "What are the diferent countri with singrs above age 20 and bilow 40 are there, please?"
#question = "How many singers do we have?"
#question = "What is the average, minimum, and maximum age for all French singers?"
#question = "What is the number of carsw ith over 6 cylinders?"
question = "How many pets are owned by students that have an age greater than 20?"

agent = NatQLEngine(load_test_db_files_from_spider('pets_1'), debug=True)
result = agent.get_answer(question)
print(json.dumps(result, indent=4))
