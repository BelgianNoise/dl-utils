import re

def parse_filename(
  input: str,
  lang: str = 'nl',
) -> str:
  '''
  Parse a string into a valid filename
  '''
  filename = input

  special_char_map = {
    'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
    'å': 'a', 'æ': 'ae', 'ç': 'c', 'è': 'e', 'é': 'e',
    'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
    'ð': 'd', 'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o',
    'ö': 'o', 'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
    'ý': 'y', 'ÿ': 'y',
  }
  for char, replacement in special_char_map.items():
    filename = re.sub(char, replacement, filename)

  # Replace & with 'En'
  filename = re.sub(r'&', ' En ' if lang == 'nl' else ' And ', filename)
  # Replace non-alphanumeric characters with '.'
  filename = re.sub(r'[^a-zA-Z0-9@]', '.', filename)
  # Replace multiple '.' with a single '.'
  filename = re.sub(r'\.{2,}', '.', filename)
  # Remove trailing '.'
  filename = re.sub(r'\.$', '', filename)
  # Remove leading '.'
  filename = re.sub(r'^\.', '', filename)
  # Replace 'Aflevering' with 'E'
  filename = re.sub('Aflevering', 'E', filename)
  # Replace 'Seizoen' with 'S'
  filename = re.sub('Seizoen', 'S', filename)
  # Remove '.' between S and season number
  filename = re.sub(r'S\.(\d{1,4})', lambda x: f'S{x.group(1)}', filename)
  # Remove '.' between E and episode number
  filename = re.sub(r'[^a-zA-Z][EeAa]\.(\d{1,4})', lambda x: f'E{x.group(1)}', filename)
  # Remove the '.' in between S and E
  filename = re.sub(r'S(\d{1,4})\.E\d{1,4}', lambda x: f'S{x.group(1)}E', filename)
  # Capitalize first letter of each word
  filename = '.'.join([word.capitalize() for word in filename.split('.')])
  # Make sure S01E01 is formatted correctly
  filename = re.sub(r'[Ss](\d{1,4})[AaEe](\d{1,4})', lambda x: f'S{x.group(1).zfill(2)}E{x.group(2).zfill(2)}', filename)

  return filename
