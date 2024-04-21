import os
import subprocess
from loguru import logger

from ..models.dl_request_platform import DLRequestPlatform
from .binaries import get_path_to_binary

def download_video(
  mpd_url: str,
  filename: str,
  platform: DLRequestPlatform,
  preferrred_quality: str = '1080',
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
  command = [get_path_to_binary('n-m3u8dl-re')]
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
