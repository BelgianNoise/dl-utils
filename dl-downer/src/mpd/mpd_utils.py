import re

def transform_mpd_time_to_milisecondsseconds(time: str):
  '''
  Transforms "PT3459.400S" into 3459400
  Transforms "PT1H" into 3600000
  Transforms "PT1M" into 60000
  '''
  # use regex to extract hours minutes and seconds
  hours = re.search(r'(\d+)H', time)
  minutes = re.search(r'(\d+)M', time)
  seconds = re.search(r'(\d+(\.\d+)?)S', time)
  # convert to milliseconds
  total_milliseconds = 0
  if hours is not None:
    total_milliseconds += int(hours.group(1)) * 60 * 60 * 1000
  if minutes is not None:
    total_milliseconds += int(minutes.group(1)) * 60 * 1000
  if seconds is not None:
    total_milliseconds += int(float(seconds.group(1)) * 1000)
  return total_milliseconds