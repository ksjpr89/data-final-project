from pathlib import Path
from bs4 import BeautifulSoup
import re

html_path = Path('/home/ubuntu/browser_html/airport_co_kr_airportYearStats.do_1779414497472.html')
out_path = Path('/home/ubuntu/data_final_analysis_work/reanalysis/outputs/kac_airport_stats_html_endpoints.txt')
html = html_path.read_text(encoding='utf-8', errors='ignore')
soup = BeautifulSoup(html, 'html.parser')
lines = []
lines.append(f'HTML path: {html_path}')
lines.append(f'Length: {len(html)}')

# Script sources and inline snippets containing likely endpoint/action names
lines.append('\n[script src]')
for s in soup.find_all('script'):
    src = s.get('src')
    if src:
        lines.append(src)

patterns = [
    'excel', 'Excel', 'download', 'Down', 'stats', 'Stats', 'airport', 'Airport', 'ajax', '.do', 'yearStats', 'frFlightStatsCon'
]
lines.append('\n[inline matches]')
for s in soup.find_all('script'):
    txt = s.get_text('\n')
    if any(p in txt for p in patterns):
        for m in re.finditer(r'.{0,120}(?:excel|Excel|download|Down|stats|Stats|airport|Airport|ajax|yearStats|frFlightStatsCon|\.do).{0,180}', txt):
            snippet = re.sub(r'\s+', ' ', m.group(0)).strip()
            if snippet:
                lines.append(snippet)

lines.append('\n[forms]')
for form in soup.find_all('form'):
    lines.append(str({k: form.get(k) for k in ['id','name','action','method']}))
    for inp in form.find_all(['input','select','button']):
        lines.append('  ' + str({k: inp.get(k) for k in ['tag','id','name','value','type','class','onclick']} | {'tag': inp.name, 'text': inp.get_text(strip=True)[:80]}))

lines.append('\n[links/buttons containing excel/search]')
for tag in soup.find_all(['a','button','input']):
    text = tag.get_text(' ', strip=True) or tag.get('value','') or ''
    attrs = ' '.join([str(tag.get(k,'')) for k in ['id','class','href','onclick','name','value']])
    if any(w in (text + ' ' + attrs).lower() for w in ['엑셀','excel','검색','search','download','down']):
        lines.append(str({'tag': tag.name, 'text': text, 'attrs': {k: tag.get(k) for k in ['id','class','href','onclick','name','value','type']}}))

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text('\n'.join(lines), encoding='utf-8')
print(out_path)
