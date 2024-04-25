def find_wv_pssh_offset(raw: bytes) -> str:
  print('Searching pssh offset')
  offset = raw.rfind(b'pssh')
  return raw[offset - 4:offset - 4 + raw[offset - 1]]


def to_pssh(content: bytes) -> str:
  wv_offset = find_wv_pssh_offset(content)
  return base64.b64encode(wv_offset).decode()


def from_file(file_path: str) -> str:
  print('Extracting PSSH from init file:', file_path)
  return to_pssh(Path(file_path).read_bytes())


def get_pssh(keyId):
  array_of_bytes = bytearray( b'\x00\x00\x002pssh\x00\x00\x00\x00')
  array_of_bytes.extend(bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed"))
  array_of_bytes.extend(b'\x00\x00\x00\x12\x12\x10')
  array_of_bytes.extend(bytes.fromhex( keyId.replace("-", "")))
  return base64.b64encode(bytes.fromhex(array_of_bytes.hex()))

# entry call
def return_pssh(kid):
  kid = kid.replace('-', '')
  assert len(kid) == 32 and not isinstance(kid, bytes), "wrong KID length"
  return ("PSSH {}".format(get_pssh(kid).decode('utf-8')))
    