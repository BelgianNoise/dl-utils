import os

def get_path_to_binary(binary_name):
  """
  Get the path to a binary in the binaries directory.
  """
  p = os.getenv('BINARIES_FOLDER', './binaries')
  if not p.endswith('/'):
    p += '/'
  p += binary_name

  return p
