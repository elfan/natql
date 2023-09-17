import re

def get_plural_term(noun):
  """
  check if noun is already plural then return unchanged.
  several rules from https://users.monash.edu/~damian/papers/HTML/Plurals.html
  - add s by default
  - ss --> sses
  - y --> ies, except (vowel)y --> ys, except soliloquy -> ies
  - irregular, e.g. criterion --> criteria, stigma -> stigmata, ox -> oxen, nucleus -> nuclei, matrix -> matrices
  """
  if noun == '': return ''

  # check if noun is already plural then return unchanged
  if re.search(r'(?:ois|sheep|deer|pox|ese|itis|men|ice|eeth?|eese|zoa|[csx]es|eaux|ieux|nges|[cs]hes|sses|[aeo]lves|[^d]eaves|arves|[nlw]ives|[aeiou]ys|ies|oes|eaus|children|foxes|oxen|ii|nuclei|est|[^us]s)$', noun):
    return noun

  # no plural
  noun, replaced = re.subn(r'(ois|sheep|deer|pox|ese|itis)$', '\1', noun)
  if replaced: return noun

  # return the plural
  noun, replaced = re.subn(r'man$', r'men', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'ouse$', r'ice', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'oot(h)$', r'eet\1', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'oose$', r'eese', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'zoon$', r'zoa', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'([csx])is$', r'\1es', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'trix$', r'trices', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'eau$', r'eaux', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'iea$', r'ieux', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'([iay])nx$', r'\1nges', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'([cs])h$', r'\1hes', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'ss$', r'sses', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'([aeo]l|[^d]ea|ar)f$', r'\1ves', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'([nlw]i)fe$', r'\1ves', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'([aeiou])y$', r'\1ys', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'y$', r'ies', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'o$', r'oes', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'eau$', r'eaus', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'child$', r'children', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'fox$', r'foxes', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'ox$', r'oxen', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'(ius|ie)$', r'ii', noun)
  if replaced: return noun

  noun, replaced = re.subn(r'nucleus$', r'nuclei', noun)
  if replaced: return noun

  # return the default plural
  return noun + 's'
