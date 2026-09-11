import os
import re
import urllib.parse
from typing import List
from loguru import logger

import requests

from ..models.dl_request_platform import DLRequestPlatform
from ..mpd.mpd import MPD
from .subtitles import parse_vtt, cues_to_srt, SubtitleCue


def download_subs_mpd(
  mpd: MPD,
  filename: str,
  platform: DLRequestPlatform,
  ignore_periods: List[str] = [],
  select_subtitle: str = 'all',
) -> List[str]:
  '''Download GoPlay's per-period VTT subtitles and merge them into SRT files.

  GoPlay serves one VTT file per content period. The video is assembled by
  concatenating those content periods back-to-back (ad periods removed), so the
  subtitle track must use the same exact period boundaries. N_m3u8DL-RE truncates
  period durations when merging subtitles, which makes the track drift out of
  sync after each ad break; downloading and merging the VTT files ourselves with
  the manifest's exact period durations avoids that drift.

  :return: list of written SRT file paths (one per subtitle language)
  '''
  save_dir = os.getenv('DOWNLOADS_FOLDER', './downloads')
  if not save_dir.endswith('/'):
    save_dir += '/'
  save_dir += platform.value
  os.makedirs(save_dir, exist_ok=True)

  cues_by_lang: dict[str, List[SubtitleCue]] = {}
  cumulative_ms = 0

  for period in mpd.periods:
    if any(re.match(pattern, period.id or '') for pattern in ignore_periods):
      continue

    for adaptation_set in period.adaptation_sets:
      if adaptation_set.mime_type != 'text/vtt':
        continue

      lang = adaptation_set.lang or adaptation_set.id or 'sub'
      if select_subtitle != 'all' and lang != select_subtitle:
        continue

      vtt_url = None
      for representation in adaptation_set.representations:
        if representation.base_url:
          vtt_url = urllib.parse.urljoin(mpd.base_url, representation.base_url)
          break

      if vtt_url is None:
        logger.warning(f'No VTT URL found for subtitle language {lang} in period {period.id}')
        continue

      logger.debug(f'Downloading subtitles ({lang}) for period {period.id}: {vtt_url}')
      response = requests.get(vtt_url)
      response.raise_for_status()

      shifted = [
        (start + cumulative_ms, end + cumulative_ms, text)
        for start, end, text in parse_vtt(response.text)
      ]
      cues_by_lang.setdefault(lang, []).extend(shifted)

    if period.duration is None:
      logger.warning(f'Period {period.id} has no duration, assuming 0ms')
      continue
    cumulative_ms += period.duration

  subtitle_files = []
  for lang, cues in cues_by_lang.items():
    if not cues:
      continue
    srt_path = os.path.join(save_dir, f'{filename}.{lang}.srt')
    with open(srt_path, 'w', encoding='utf-8') as f:
      f.write(cues_to_srt(cues))
    subtitle_files.append(srt_path)
    logger.info(f'Wrote subtitles ({lang}) to {srt_path}')

  return subtitle_files
