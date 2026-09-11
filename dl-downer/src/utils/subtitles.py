import re
from html import unescape
from typing import List, Tuple


# A subtitle cue: (start_milliseconds, end_milliseconds, text)
SubtitleCue = Tuple[int, int, str]


_VTT_TIMING_LINE = re.compile(
  r'^(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3})\s+-->\s+(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3})(?P<settings>.*)$'
)
_TAG = re.compile(r'<[^>]+>')


def timestamp_to_milliseconds(timestamp: str) -> int:
  '''Convert 'HH:MM:SS.mmm' (VTT) or 'HH:MM:SS,mmm' (SRT) to milliseconds.'''
  parts = timestamp.split(':')
  if len(parts) == 2:
    hours, minutes = 0, int(parts[0])
    seconds_and_milliseconds = parts[1]
  else:
    hours, minutes, seconds_and_milliseconds = int(parts[0]), int(parts[1]), parts[2]
  seconds, milliseconds = re.split(r'[.,]', seconds_and_milliseconds)
  return (
    hours * 60 * 60 * 1000
    + minutes * 60 * 1000
    + int(seconds) * 1000
    + int(milliseconds)
  )


def milliseconds_to_timestamp(milliseconds: int) -> str:
  '''Convert milliseconds to an SRT-style 'HH:MM:SS,mmm' timestamp.'''
  milliseconds = max(milliseconds, 0)
  hours, milliseconds = divmod(milliseconds, 60 * 60 * 1000)
  minutes, milliseconds = divmod(milliseconds, 60 * 1000)
  seconds, milliseconds = divmod(milliseconds, 1000)
  return f'{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}'


def parse_vtt(vtt_text: str) -> List[SubtitleCue]:
  '''Parse a WebVTT document into a list of (start_ms, end_ms, text) cues.'''
  cues: List[SubtitleCue] = []
  lines = vtt_text.splitlines()
  total = len(lines)
  i = 0

  # Skip everything before the first cue (WEBVTT header, NOTE/STYLE/REGION blocks).
  while i < total:
    if _VTT_TIMING_LINE.match(lines[i].strip()):
      break
    i += 1

  while i < total:
    match = _VTT_TIMING_LINE.match(lines[i].strip())
    if match is None:
      i += 1
      continue

    start = timestamp_to_milliseconds(match.group('start'))
    end = timestamp_to_milliseconds(match.group('end'))
    i += 1

    text_lines = []
    while i < total and lines[i].strip() != '':
      text_lines.append(_TAG.sub('', lines[i].strip()))
      i += 1

    text = unescape('\n'.join(text_lines))
    cues.append((start, end, text))
    i += 1

  return cues


def cues_to_srt(cues: List[SubtitleCue]) -> str:
  '''Serialize a list of (start_ms, end_ms, text) cues to SRT.'''
  blocks = []
  for index, (start, end, text) in enumerate(cues, 1):
    blocks.append(
      f'{index}\n'
      f'{milliseconds_to_timestamp(start)} --> {milliseconds_to_timestamp(end)}\n'
      f'{text}\n'
    )
  return '\n'.join(blocks)
