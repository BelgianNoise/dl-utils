import os
import subprocess
from typing import List
from loguru import logger

from ..models.dl_request_platform import DLRequestPlatform

def download_video_nre(
  mpd_url: str,
  filename: str,
  platform: DLRequestPlatform,
  preferrred_quality: str,
  keys={},
  select_audio: str = 'all',
  select_subtitle: str = 'all',
  select_video: str = None,
  extra_args: list = [],
) -> str:
  '''
  Download, decrypt, and merge file using N_m3u8DL-RE

  :return: Path to downloaded file
  '''
  command = ['n-m3u8dl-re']
  for kid, key in keys.items():
    command.append('--key')
    command.append(f'{kid}:{key}')

  save_dir = os.getenv('DOWNLOADS_FOLDER', './downloads')
  if not save_dir.endswith('/'):
    save_dir += '/'
  save_dir += platform.value

  # if preferred quality matcher only consists of digits
  if select_video is not None:
    command.extend(['--select-video', select_video])
  elif preferrred_quality:
    if preferrred_quality.isdigit():
      preferrred_quality = f'res=".*{preferrred_quality}.*"'
    command.extend(['--select-video', preferrred_quality])
  else:
    command.extend(['--auto-select'])

  command.extend([
    '--select-audio', select_audio,
    '--select-subtitle', select_subtitle,
    '--concurrent-download',
    '--no-log',
    '--tmp-dir', f'./tmp/{platform.value}',
    '--mux-after-done', 'format=mkv:muxer=ffmpeg',
    '--save-dir', save_dir,
    '--save-name', filename,
    mpd_url])
  
  command.extend(extra_args)

  logger.debug(f'Calling binary ... {command}')
  subprocess.run(command)

  logger.info(f'Finished downloading {filename}')

  return f'{save_dir}/{filename}.mkv'

def download_subs_nre(
  mpd_url: str,
  filename: str,
  platform: DLRequestPlatform,
  keys={},
  select_subtitle: str = 'all',
  sub_format: str = 'SRT',
  extra_args: list = [],
) -> List[str]:
  command = ['n-m3u8dl-re']
  
  # Add decryption keys if provided
  for kid, key in keys.items():
    command.append('--key')
    command.append(f'{kid}:{key}')

  save_dir = os.getenv('DOWNLOADS_FOLDER', './downloads')
  if not save_dir.endswith('/'):
    save_dir += '/'
  save_dir += platform.value

  # Configure subtitle-specific options
  command.extend([
    '--sub-only',  # Download only subtitles
    '--select-subtitle', select_subtitle,
    '--sub-format', sub_format,
    '--auto-subtitle-fix',  # Automatically fix subtitle timing issues
    '--concurrent-download',
    '--no-log',
    '--tmp-dir', f'./tmp/{platform.value}',
    '--save-dir', save_dir,
    '--save-name', filename,
    mpd_url
  ])
  
  command.extend(extra_args)

  logger.debug(f'Calling binary for subtitles ... {command}')
  subprocess.run(command)

  logger.info(f'Finished downloading subtitles for {filename}')

  # Find all subtitle files that were created
  # n-m3u8dl-re typically creates files with patterns like filename_lang.srt
  subtitle_files = []
  for file in os.listdir(save_dir):
    if file.startswith(filename) and file.lower().endswith(('.srt', '.vtt')):
      subtitle_files.append(os.path.join(save_dir, file))
  
  if not subtitle_files:
    logger.warning(f'No subtitle files found for {filename}')
  else:
    logger.info(f'Found {len(subtitle_files)} subtitle files: {subtitle_files}')

  return subtitle_files