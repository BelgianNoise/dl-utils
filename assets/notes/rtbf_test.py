from pathlib import Path
import subprocess
import requests
import json
import re
import os

files_to_delete = ["key.txt"]
for file_name in files_to_delete:
  if os.path.exists(file_name):
    os.remove(file_name)
    print(f"{file_name} file successfully deleted.")

m3u8DL_RE = 'N_m3u8DL-RE.exe'

def replace_invalid_chars(title: str) -> str:
    invalid_chars = {'<': '\u02c2', '>': '\u02c3',
    ':': '\u02d0', '"': '\u02ba', '/': '\u2044',
    '\\': '\u29f9', '|': '\u01c0', '?': '\u0294',
    '*': '\u2217'}
    
    return ''.join(invalid_chars.get(c, c) for c in title)

print('\ntest link: https://www.rtbf.be/article/tour-de-belgique-mathieu-van-der-poel-decroche-l-etape-reine-a-durbuy-en-leader-solitaire-11214483\n')

link = input('link: ')

import requests

headers1 = {
  'authority': 'exposure.api.redbee.live',
  'content-type': 'application/json',
  'origin': 'https://www.rtbf.be',
  'referer': 'https://www.rtbf.be/',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

json_data1 = {
  'device': {
    'height': 0,
    'width': 0,
    'model': '',
    'name': '',
    'os': '',
    'osVersion': '',
    'manufacturer': '',
    'type': 'WEB',
  },
  'deviceId': '123',
}

response1 = requests.post('https://exposure.api.redbee.live/v2/customer/RTBF/businessunit/Auvio/auth/anonymous', headers=headers1,json=json_data1).json()

sessionToken = response1['sessionToken']

import requests

headers2 = {
  'authority': 'www.rtbf.be',
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

response2 = requests.get(link, headers=headers2).text

grab_json = re.findall(r'<script id=\"__NEXT_DATA__\" type=\"application/json\">(.*)</script></body></html>', response2)[0].strip()
grab_json = json.loads(grab_json)

assetId = grab_json['props']['pageProps']['article']['blocks'][0]['content']['media']['assetId']

title = grab_json['props']['pageProps']['article']['blocks'][0]['content']['media']['title']
title = replace_invalid_chars(title)
print(f'\n{title}')

import requests

headers3 = {
    'authority': 'exposure.api.redbee.live',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'authorization': f'Bearer {sessionToken}',
    'content-type': 'application/json',
    'origin': 'https://www.rtbf.be',
    'referer': 'https://www.rtbf.be/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

response3 = requests.get('https://exposure.api.redbee.live/v2/customer/RTBF/businessunit/Auvio/entitlement/'+assetId+'/play?supportedFormats=dash&supportedDrms=widevine',headers=headers3).json()

mpd = response3['formats'][0]['mediaLocator']
lic_url = response3['formats'][0]['drm']['com.widevine.alpha']['licenseServerUrl']

import requests

headers04 = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

response04 = requests.get(mpd, headers=headers04).text

pssh = re.findall(r'<cenc:pssh>(.{20,170})</cenc:pssh>', response04)[0].strip()
print(f'\n{pssh}')

import requests

headers_cdrm = {
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://cdrm-project.com',
    'Referer': 'https://cdrm-project.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

json_data_cdrm = {
    'license': lic_url,
    'headers': f'connection: keep-alive\n',
    'pssh': pssh,
    'buildInfo': '',
    'proxy': '',
    'cache': True,
}

cdrm_resp = requests.post('https://cdrm-project.com/wv', headers=headers_cdrm, json=json_data_cdrm).text

from bs4 import BeautifulSoup

print(f'\n{cdrm_resp}')
soup = BeautifulSoup(cdrm_resp, 'html.parser')
li_s = soup.find_all('li')
keys = []

for li in li_s:
  keys.append(li.text.strip())

key_s = ' '.join(['--key ' + key for key in keys])
print(f'\nkey(s):\n{key_s}')

print(key_s, file=open("key.txt", "w"))

with open("key.txt", "r") as fs:
  ke_ys = fs.readlines()
  ke_ys = ke_ys[0].strip().split()

print()
subprocess.run([m3u8DL_RE,
  '-M', 'format=mkv:muxer=ffmpeg',
  '--concurrent-download',
  '--auto-select', 
  '--del-after-done',
  '--log-level', 'INFO',
  '--save-name', 'video',
  mpd, *ke_ys])

try:
    Path('video.mkv').rename(''+title+'.mkv')
    print(f'{title}.mkv \nall done!\n')
except FileNotFoundError:
    print("[ERROR] no mkv file")                
