import re


def parse_filename_fields(filename: str) -> dict:
  '''
  Extract title, season, and episode from a filename using regex.

  Tries common patterns in order:
    1. S01E03 / s1e3 / S01.E03 / S01A03 (Dutch)
    2. 1x03
    3. Season 1 Episode 3 / Seizoen 1 Aflevering 3

  Returns dict with 'title', 'season', 'episode'.
  Season/episode are zero-padded strings or None.
  '''
  result = {
    'title': filename,
    'season': None,
    'episode': None,
  }

  # Pattern 1: S01E03, s1e3, S01.E03, S01A03
  match = re.search(r'[.\s_-]*[Ss](\d{1,4})[.\s_-]*[EeAa](\d{1,4})', filename)
  if match:
    result['season'] = match.group(1).zfill(2)
    result['episode'] = match.group(2).zfill(2)
    result['title'] = filename[:match.start()].rstrip('.-_ ')
    if result['title']:
      return result

  # Pattern 2: 1x03
  match = re.search(r'[.\s_-]*(\d{1,2})x(\d{1,4})', filename)
  if match:
    result['season'] = match.group(1).zfill(2)
    result['episode'] = match.group(2).zfill(2)
    result['title'] = filename[:match.start()].rstrip('.-_ ')
    if result['title']:
      return result

  # Pattern 3: Season/Seizoen + Episode/Aflevering/Ep
  match = re.search(
    r'[.\s_-]*(?:Season|Seizoen)[.\s_-]*(\d{1,4})[.\s_-]*(?:Episode|Aflevering|Ep)[.\s_-]*(\d{1,4})',
    filename,
    re.IGNORECASE,
  )
  if match:
    result['season'] = match.group(1).zfill(2)
    result['episode'] = match.group(2).zfill(2)
    result['title'] = filename[:match.start()].rstrip('.-_ ')
    if result['title']:
      return result

  # No season/episode found
  result['title'] = filename
  return result
