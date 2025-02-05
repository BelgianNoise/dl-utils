import os
import sys
from loguru import logger

def validate_server_structure():
  '''
  Check if all necessary files and folders are present in the server's directory.
  '''

  logger.info('Validating server structure...')

  cdm = os.getenv('CDM_FILE_PATH', './cdm/cdm.wvd')
  # Make sure there is a cdm file
  for f in [cdm]:
    if not os.path.isfile(f):
      print(f"File {f} not found")
      sys.exit(1)

  storage_states_folder = os.getenv('STORAGE_STATES_FOLDER', "./storage_states")
  dl_folder = os.getenv('DOWNLOADS_FOLDER', "./downloads")
  for f in [storage_states_folder, dl_folder]:
    if not os.path.isdir(f):
      os.mkdir(f)
  
  logger.info('Server structure validated')
