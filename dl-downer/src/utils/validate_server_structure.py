import os
import sys

from .binaries import get_path_to_binary

def validate_server_structure():
  '''
  Check if all necessary files and folders are present in the server's directory.
  '''

  # Check if all binaries are present
  m3u8dl = get_path_to_binary("n-m3u8dl-re.exe")
  ffmpeg = get_path_to_binary("ffmpeg.exe")
  mkvmerge = get_path_to_binary("mkvmerge.exe")
  mp4decrypt = get_path_to_binary("mp4decrypt.exe")
  cdm = os.getenv('CDM_FILE_PATH', './cdm/cdm.wvd')

  for f in [m3u8dl, ffmpeg, mkvmerge, mp4decrypt, cdm]:
    if not os.path.isfile(f):
      print(f"'{f}' not found.")
      sys.exit(1)

  cook_folder = os.getenv('COOKIES_FOLDER', "./cookies")
  dl_folder = os.getenv('DOWNLOADS_FOLDER', "./downloads")
  for f in [cook_folder, dl_folder]:
    if not os.path.isdir(f):
      os.mkdir(f)
