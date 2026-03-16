import os
import re
from datetime import datetime
from loguru import logger
from .filename import parse_filename


DEFAULT_PATTERN = '{platform}/{title}.S{season}E{episode}.{extension}'


def apply_output_pattern(
  title: str,
  platform: str,
  extension: str,
  suggested_filepath: str,
  current_filepath: str = None,
  season: str = None,
  episode: str = None,
) -> str:
  '''
  Build the final output file path by applying DL_OUTPUT_PATTERN.

  The pattern is relative to DOWNLOADS_FOLDER. Segments containing
  unresolved {variables} are stripped (e.g. .S{season}E{episode}
  disappears when season/episode are None).

  Falls back to suggested_filepath on pattern errors or path traversal.
  '''
  pattern = os.getenv('DL_OUTPUT_PATTERN', DEFAULT_PATTERN)

  if '..' in pattern:
    logger.warning(f'Path traversal in DL_OUTPUT_PATTERN: {pattern}. Using fallback.')
    return suggested_filepath

  sanitized_title = parse_filename(title)

  variables = {
    'platform': platform,
    'title': sanitized_title,
    'title_spaced': sanitized_title.replace('.', ' '),
    'extension': extension,
  }
  if season is not None:
    variables['season'] = season
  if episode is not None:
    variables['episode'] = episode

  path_segments = pattern.split('/')
  resolved_segments = []

  for segment in path_segments:
    resolved = _resolve_segment(segment, variables)
    if resolved:
      resolved_segments.append(resolved)

  if not resolved_segments:
    logger.warning(f'Pattern resolved to empty. Using fallback: {suggested_filepath}')
    return suggested_filepath

  downloads_folder = os.getenv('DOWNLOADS_FOLDER', './downloads')
  relative_path = '/'.join(resolved_segments)
  absolute_path = os.path.normpath(os.path.join(downloads_folder, relative_path))
  absolute_downloads = os.path.normpath(os.path.abspath(downloads_folder))

  # Ensure resolved path stays within DOWNLOADS_FOLDER
  if not os.path.abspath(absolute_path).startswith(absolute_downloads):
    logger.warning(f'Resolved path escapes DOWNLOADS_FOLDER. Using fallback: {suggested_filepath}')
    return suggested_filepath

  # If the file is already at the resolved location, return as-is (skip dedup)
  if current_filepath and os.path.abspath(current_filepath) == os.path.abspath(absolute_path):
    return absolute_path

  # Deduplicate: append timestamp if file already exists
  if os.path.exists(absolute_path):
    name, ext = os.path.splitext(absolute_path)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    absolute_path = f'{name}-{timestamp}{ext}'

  logger.debug(f'Output pattern resolved: {pattern} -> {absolute_path}')
  return absolute_path


def _resolve_segment(segment: str, variables: dict) -> str:
  '''
  Resolve a path segment by splitting on '.' and dropping
  dot-groups that still contain unresolved {placeholders}.
  '''
  dot_groups = segment.split('.')
  resolved_groups = []

  for group in dot_groups:
    resolved = _substitute_variables(group, variables)
    if re.search(r'\{[^}]+\}', resolved):
      continue
    if resolved:
      resolved_groups.append(resolved)

  return '.'.join(resolved_groups)


def _substitute_variables(text: str, variables: dict) -> str:
  '''Replace {key} placeholders with values from variables dict.'''
  def replacer(match):
    key = match.group(1)
    return variables[key] if key in variables else match.group(0)

  return re.sub(r'\{([^}]+)\}', replacer, text)
