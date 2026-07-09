import base64
import os
import re
from loguru import logger
from pyplayready.cdm import Cdm as PlayReadyCdm
from pyplayready.device import Device as PlayReadyDevice
from pyplayready.system.pssh import PSSH as PlayReadyPSSH


class Local_PlayReady_CDM():
  def __init__(self, prd_file=None):
    '''
    Create a PlayReady CDM instance using pyplayready and a local .prd file
    '''
    if prd_file is None:
      prd_file = os.getenv('CDM_PRD_FILE_PATH', './cdm/cdm.prd')
    self.device = PlayReadyDevice.load(prd_file)
    self.cdm = PlayReadyCdm.from_device(self.device)
    self.session_id = self.cdm.open()

  def generate_challenge(self, pssh_b64):
    '''
    Generate a PlayReady challenge

    :return: PlayReady challenge (typically XML text payload)
    '''
    pssh = PlayReadyPSSH(pssh_b64)
    wrm_header = pssh.wrm_headers[0]
    challenge = self.cdm.get_license_challenge(
      self.session_id,
      wrm_header,
    )

    if isinstance(challenge, bytes):
      logger.debug(f'PlayReady challenge: {base64.b64encode(challenge)}')
    else:
      logger.debug(f'PlayReady challenge: {challenge}')

    return challenge

  def decrypt_response(self, response):
    '''
    Generate keys based on PlayReady response

    :return: dictionary of kid:key
    '''
    try:
      self.cdm.parse_license(self.session_id, response)
    except TypeError as e:
      # Work around pyplayready revocation parsing bug on some versions.
      if 'from_bytes() missing required argument' not in str(e):
        raise
      if not isinstance(response, str):
        raise

      response_without_revinfo = re.sub(
        r'<RevInfo>.*?</RevInfo>',
        '',
        response,
        flags=re.DOTALL,
      )
      if response_without_revinfo == response:
        raise

      logger.warning('Retrying PlayReady license parse without RevInfo due to pyplayready revocation parsing bug')
      self.cdm.parse_license(self.session_id, response_without_revinfo)

    keys = {key.key_id.hex:key.key.hex() for key in self.cdm.get_keys(self.session_id)}
    logger.debug(f'PlayReady keys: {keys}')

    return keys

  def parse_license(self, license):
    return self.decrypt_response(license)

  def close(self):
    '''
    Close the cdm
    '''
    self.cdm.close(self.session_id)
