import json
import re
import string

from textblob import TextBlob

from plural_engine import get_plural_term


def make_list_re(re_str):
  return re_str + '(?:(?:,| and|, and) *' + re_str + ')*'

def auto_discover_foreign_keys(table_schema):
  """
  from a schema of tables and their columns, find out the foreign key relationships
  """

def auto_discover_primary_keys(table_schema):
  """
  if table name is "singer" then the candidates are "id", "singer_id", "singer"
  if column name has more than one suffix "_id", possibility they are foreign keys
  """

def correct_sentence_spelling(sentence: string) -> string:
  # fix incorrect auto correct

  tb = TextBlob(sentence)
  corrected = str(tb.correct())

  if (corr_match := re.search(r'(\w+) +it ', corrected, flags=re.IGNORECASE)) and (match := re.search(corr_match.group(1) + r'w +ith ', sentence, flags=re.IGNORECASE)):
    corrected = re.sub(corr_match.group(1) + r' +it ', corr_match.group(1) + ' with ', corrected, flags=re.IGNORECASE)

  if re.search(r'^that ', corrected, flags=re.IGNORECASE) and (match := re.search(r'^what ', sentence, flags=re.IGNORECASE)):
    corrected = re.sub(r'^that ', match.group(0), corrected, flags=re.IGNORECASE)
  elif re.search(r'^now ', corrected, flags=re.IGNORECASE) and (match := re.search(r'^how ', sentence, flags=re.IGNORECASE)):
    corrected = re.sub(r'^now ', match.group(0), corrected, flags=re.IGNORECASE)
  elif re.search(r'^how ', corrected, flags=re.IGNORECASE) and (match := re.search(r'^show ', sentence, flags=re.IGNORECASE)):
    corrected = re.sub(r'^how ', match.group(0), corrected, flags=re.IGNORECASE)
  elif re.search(r'^mind ', corrected, flags=re.IGNORECASE) and (match := re.search(r'^find ', sentence, flags=re.IGNORECASE)):
    corrected = re.sub(r'^mind ', match.group(0), corrected, flags=re.IGNORECASE)

  return corrected

def normalize_question(str):
  """
  make sure all spaces are one space
  remove optional dot or comma
  trim
  """
  str = re.sub(r' +', ' ', str)   # make sure there is no multiple spaces
  str = re.sub(r'[.,?]$', '', str) # remove '.' or ',' or '?' at the end
  str = str.strip()               # trim spaces
  return str

def get_normal_term(str):
  """
  replace "_" with space  
  """
  str = re.sub(r'_', ' ', str)    # replace '_' with space
  str = normalize_question(str)
  return str

def file_get_contents(file_name):
  with open(file_name, 'r', encoding='utf8') as f:
    return f.read()

def file_get_json(file_name):
  with open(file_name, 'r', encoding='utf8') as f:
    return json.load(f)

def get_non_empty_val(dictionary):
  return dict((k, v) for k, v in dictionary.items() if v is not None)

def unique(list):
  unique_list = []
  for item in list:
    if item not in unique_list:
      unique_list.append(item)
  return unique_list

def find_sub_list(sub_list, list):
  sub_len = len(sub_list)
  for idx in (i for i, e in enumerate(list) if e == sub_list[0]):
    if list[idx:idx + sub_len] == sub_list:
      return idx
