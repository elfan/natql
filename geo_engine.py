import json
import os
import re
import string

from util import file_get_json, unique

def get_country_info():
  cache_file = 'cache/get_country_info.json'
  if 0 and os.path.exists(cache_file):
    return file_get_json(cache_file)

  f = open('qdata/geo_names.txt', 'r', encoding='utf8')
  lines = f.readlines()
  f.close()

  countries = {}
  for line in lines:
    if re.search(r'^\s*#', line):
      continue
    if not re.search(r'^\{.+\}$', line):
      continue
    info = json.loads(line)
    for adj in info.get('adjectives'):
      adj = adj.lower()
      if not countries.get(adj):
        countries[adj] = []
      countries[adj].append(info.get('name'))
    for dem in info.get('demonyms'):
      dem = dem.lower()
      if not countries.get(dem):
        countries[dem] = []
      countries[dem].append(info.get('name'))

  for key in countries:
    countries[key] = unique(countries[key])

  with open(cache_file, 'w', encoding='utf8') as f:
    f.write(json.dumps(countries, indent=2))

  return countries

countries_dict = None
def get_country_of(countryan: string) -> string:
  global countries_dict
  if countries_dict is None:
    countries_dict = get_country_info()

  country = countries_dict.get(countryan.lower())
  if country is not None and len(country) > 0:
    return country

  return None
