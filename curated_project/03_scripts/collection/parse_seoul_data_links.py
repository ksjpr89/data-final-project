from __future__ import annotations

import re
from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path('/home/ubuntu/browser_html/data_seoul_go_kr_datasetView.do_1779716598798.html')
text = html_path.read_text(encoding='utf-8', errors='ignore')
soup = BeautifulSoup(text, 'html.parser')

print('anchors containing LOCAL_PEOPLE_DONG:')
for a in soup.find_all('a'):
    label = a.get_text(' ', strip=True)
    href = a.get('href') or ''
    onclick = a.get('onclick') or ''
    if 'LOCAL_PEOPLE_DONG' in label or 'LOCAL_PEOPLE_DONG' in href or 'LOCAL_PEOPLE_DONG' in onclick:
        print({'label': label, 'href': href, 'onclick': onclick})

print('\nJS snippets around LOCAL_PEOPLE_DONG_202603:')
for m in re.finditer('LOCAL_PEOPLE_DONG_202603', text):
    start = max(0, m.start() - 500)
    end = min(len(text), m.end() + 500)
    print(text[start:end].replace('\n', ' ')[:1200])
    print('---')

print('\nPotential file IDs and function calls:')
patterns = [r'fn_[A-Za-z0-9_]+\([^)]*LOCAL_PEOPLE_DONG_202603[^)]*\)', r'fileNo[^,;\n]+', r'atchFileId[^,;\n]+', r'downFile[^;\n]+']
for pat in patterns:
    found = re.findall(pat, text)
    print(pat, found[:20])
