import base64
import os
from loguru import logger
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH

class Local_CDM():
  def __init__(self, wvd_file=None):
    '''
    Create a cdm instance using pywidevine and a local .wvd file
    '''
    if wvd_file is None:
      self.device = Device.load(os.getenv('CDM_FILE_PATH', './cdm/cdm.wvd'))
    else:
      self.device = Device.load(wvd_file)
    self.cdm = Cdm.from_device(self.device)
    self.session_id = self.cdm.open()

  def generate_challenge(self, pssh_b64):
    '''
    Generate a Widevine challenge

    :return: Widevine challenge in binary form
    '''
    challenge = self.cdm.get_license_challenge(self.session_id, PSSH(pssh_b64))
    logger.debug(f'Challenge: {base64.b64encode(challenge)}')

    return challenge

  def decrypt_response(self, response):
    '''
    Generate keys based on Widevine response

    :return: dictionary of kid:key
    '''
    self.cdm.parse_license(self.session_id, response)
    keys = {key.kid.hex:key.key.hex() for key in self.cdm.get_keys(self.session_id) if key.type == 'CONTENT'}
    logger.debug(f'Keys: {keys}')

    return keys

  def close(self):
    '''
    Close the cdm
    '''
    self.cdm.close(self.session_id)
