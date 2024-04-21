import re

def parse_filename(input: str) -> str:
  '''
  Parse a string into a valid filename
  '''
  filename = input
  # Replace all special characters
  invalid_chars = ['&#039;']
  for char in invalid_chars:
    filename = filename.replace(char, '')
  # Replace non-alphanumeric characters with '.'
  filename = re.sub(r'[^a-zA-Z0-9]', '.', filename)
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
