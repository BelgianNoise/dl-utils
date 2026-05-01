import os
import json
from datetime import datetime
from loguru import logger
from playwright.sync_api import Page


def _is_enabled() -> bool:
  return os.getenv('BROWSER_DIAGNOSTICS_ENABLED', 'false') == 'true'

def _get_output_folder() -> str:
  return os.getenv('BROWSER_DIAGNOSTICS_FOLDER', './diagnostics')


def attach_diagnostics_listeners(page: Page) -> None:
  '''
  Attach console and network listeners to the page for later export.
  Must be called early (right after page creation) so events are captured
  from the start. Does nothing if diagnostics are disabled.
  '''
  if not _is_enabled():
    return

  page._diagnostics_console = []
  page._diagnostics_network = []

  def on_console(msg):
    location = msg.location
    page._diagnostics_console.append({
      'type': msg.type,
      'text': msg.text,
      'url': location.get('url', ''),
      'line': location.get('lineNumber', ''),
    })

  def on_request(request):
    page._diagnostics_network.append({
      'url': request.url,
      'method': request.method,
      'headers': dict(request.headers),
      'resource_type': request.resource_type,
      'response': None,
    })

  def on_response(response):
    # Find the matching request entry and attach response info
    for entry in reversed(page._diagnostics_network):
      if entry['url'] == response.url and entry['response'] is None:
        entry['response'] = {
          'status': response.status,
          'status_text': response.status_text,
          'headers': dict(response.headers),
        }
        break

  page.on('console', on_console)
  page.on('request', on_request)
  page.on('response', on_response)


def export_browser_diagnostics(page: Page, label: str) -> None:
  '''
  Write screenshot, console logs, and network log to disk.
  Safe to call at any time — silently returns if diagnostics are disabled
  or if an error occurs during export.

  :param page: the Playwright page to capture diagnostics from
  :param label: short identifier used in the output folder name
  '''
  if not _is_enabled():
    return

  try:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(_get_output_folder(), f'{label}_{timestamp}')
    os.makedirs(output_dir, exist_ok=True)

    # Screenshot
    try:
      page.screenshot(path=os.path.join(output_dir, 'screenshot.png'), full_page=True)
      logger.debug(f'Diagnostics screenshot saved to {output_dir}')
    except Exception as e:
      logger.warning(f'Failed to capture screenshot: {e}')

    # Page URL for context
    try:
      current_url = page.url
    except Exception:
      current_url = 'unknown'

    # Console logs
    console_logs = getattr(page, '_diagnostics_console', [])
    with open(os.path.join(output_dir, 'console.json'), 'w') as f:
      json.dump({'page_url': current_url, 'messages': console_logs}, f, indent=2, default=str)

    # Network log
    network_log = getattr(page, '_diagnostics_network', [])
    with open(os.path.join(output_dir, 'network.json'), 'w') as f:
      json.dump({'page_url': current_url, 'requests': network_log}, f, indent=2, default=str)

    logger.info(f'Browser diagnostics exported to {output_dir}')

  except Exception as e:
    logger.warning(f'Failed to export browser diagnostics: {e}')
