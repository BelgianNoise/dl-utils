""" This file contains old code from VRT MAX downloaders """

def generate_pssh(content_id):
  '''
  Generate PSSH (no KID for VRTMAX)

  :return: pssh in base64
  '''
  lc = len(content_id)
  box_size = f'{lc+40:08x}' # 4 bytes
  bmff_header = '7073736800000000' # box type 'pssh' 8 bytes
  system_id = 'edef8ba979d64acea3c827dcd51d21ed' # 16 bytes
  data_size = f'{lc+8:08x}' # 4 bytes
  ending = '48e3dc959b06'
  logger.debug(f'll {len(bytes(content_id, "utf-8").hex())} {bytes(content_id, "utf-8").hex()}')
  pssh = f'{box_size}{bmff_header}{system_id}{data_size}22{lc:02x}{bytes(content_id, "utf-8").hex()}{ending}'
  pssh_b64 = base64.b64encode(bytes.fromhex(pssh)).decode()
  logger.debug(f'PSSH: {pssh_b64}')

  return pssh_b64

def generate_playerinfo():
  '''
  !! OLD CODE - NOT REQUIRED !!
  Generate an extra token to get the HD+ .mpd file from the API. Copied from:
  https://github.com/add-ons/plugin.video.vrt.nu/blob/master/resources/lib/tokenresolver.py#L282

  :return: JWT token
  '''
  try:
    # Extract JWT key id and secret from player javascript
    response = requests.get('https://player.vrt.be/vrtnu/js/main.js')
    data = response.text
    crypt_rx = re.compile(r'atob\(\"(==[A-Za-z0-9+/]*)\"')
    crypt_data = re.findall(crypt_rx, data)
    kid_source = crypt_data[0]
    secret_source = crypt_data[-1]
    kid = base64.b64decode(kid_source[::-1]).decode('utf-8')
    secret = base64.b64decode(secret_source[::-1]).decode('utf-8')

    # Extract player version
    player_version = '2.4.1'
    pv_rx = re.compile(r'playerVersion:\"(\S*)\"')
    match = re.search(pv_rx, data)
    if match:
      player_version = match.group(1)
  except:
    logger.debug('Could not extract JWT secret, download quality will be limited to SD content')
    return None

  # Generate JWT
  segments = []
  header = dict(
    alg = 'HS256',
    kid = kid
  )
  payload = dict(
    exp = time.time() + 1000,
    platform = 'desktop',
    app = dict(
      type = 'browser',
      name = 'Firefox',
      version = '102.0'
    ),
    device = 'undefined (undefined)',
    os = dict(
      name = 'Linux',
      version = 'x86_64'
    ),
    player = dict(
      name = 'VRT web player',
      version = player_version
    )
  )
  json_header = json.dumps(header).encode()
  json_payload = json.dumps(payload).encode()
  segments.append(base64.urlsafe_b64encode(json_header).decode('utf-8').replace('=', ''))
  segments.append(base64.urlsafe_b64encode(json_payload).decode('utf-8').replace('=', ''))
  signing_input = '.'.join(segments).encode()
  signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
  segments.append(base64.urlsafe_b64encode(signature).decode('utf-8').replace('=', ''))
  playerinfo = '.'.join(segments)

  logger.debug(f'Player JWT: {playerinfo}')
  return playerinfo