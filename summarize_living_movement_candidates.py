from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

BASE = Path('/home/ubuntu/data_final_analysis_work')
OUT = BASE / 'outputs'
OUT.mkdir(exist_ok=True)

CANDIDATE_NAMES = {
    '11500615': '우장산동',
    '11500620': '공항동',
    '11500603': '가양1동',
    '11500611': '발산1동',
    '11500630': '방화1동',
    '11500640': '방화2동',
    '11500641': '방화3동',
    '11500535': '등촌3동',
}

def read_csv_guess(data: bytes) -> pd.DataFrame:
    for enc in ['utf-8-sig', 'cp949', 'euc-kr', 'utf-8']:
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    raise RuntimeError('encoding failed')

rows = []
summary_parts = []
for zp in sorted((BASE / 'living_movement').glob('*.zip')):
    date = re.search(r'(20\d{6})', zp.name).group(1)
    with zipfile.ZipFile(zp) as z:
        csv_names = [n for n in z.namelist() if n.lower().endswith('.csv')]
        if not csv_names:
            continue
        df = read_csv_guess(z.read(csv_names[0]))
    df['o_code8'] = df['o_admdong_cd'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8).str[:8]
    df['d_code8'] = df['d_admdong_cd'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8).str[:8]
    df['cnt'] = pd.to_numeric(df['cnt'], errors='coerce').fillna(0)
    df['date'] = date
    df['origin_candidate'] = df['o_code8'].map(CANDIDATE_NAMES)
    df['dest_candidate'] = df['d_code8'].map(CANDIDATE_NAMES)
    inbound = df[df['dest_candidate'].notna()].copy()
    inbound['direction'] = 'inbound_to_candidate'
    inbound['candidate_dong'] = inbound['dest_candidate']
    outbound = df[df['origin_candidate'].notna()].copy()
    outbound['direction'] = 'outbound_from_candidate'
    outbound['candidate_dong'] = outbound['origin_candidate']
    internal = df[df['origin_candidate'].notna() & df['dest_candidate'].notna()].copy()
    internal['direction'] = 'candidate_internal_or_between'
    internal['candidate_dong'] = internal['dest_candidate']
    subset = pd.concat([inbound, outbound, internal], ignore_index=True)
    if not subset.empty:
        g = subset.groupby(['date','candidate_dong','direction','move_purpose'], as_index=False).agg(
            movement_population=('cnt','sum'),
            row_count=('cnt','size')
        )
        summary_parts.append(g)
    rows.append({
        'file': zp.name,
        'date': date,
        'rows_total': len(df),
        'rows_inbound_candidate': int(len(inbound)),
        'rows_outbound_candidate': int(len(outbound)),
        'cnt_inbound_candidate': float(inbound['cnt'].sum()),
        'cnt_outbound_candidate': float(outbound['cnt'].sum()),
    })

pd.DataFrame(rows).to_csv(OUT / 'living_movement_candidate_code_audit.csv', index=False, encoding='utf-8-sig')
if summary_parts:
    summary = pd.concat(summary_parts, ignore_index=True)
    summary.to_csv(OUT / 'candidate_living_movement_by_day_purpose.csv', index=False, encoding='utf-8-sig')
    pivot = summary.groupby(['candidate_dong','direction'], as_index=False)['movement_population'].mean()
    pivot.to_csv(OUT / 'candidate_living_movement_avg_daily_direction.csv', index=False, encoding='utf-8-sig')
print('done', sum(r['rows_total'] for r in rows), 'daily_files', len(rows))
