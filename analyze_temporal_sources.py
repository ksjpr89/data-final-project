from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

BASE = Path('/home/ubuntu/data_final_analysis_work')
OUT_LOCAL = BASE / 'outputs'
OUT_LOCAL.mkdir(parents=True, exist_ok=True)

# 과제 후보권역: 강서구 내 마곡·발산·공항권 중심. 실제 행정동 명칭은 자료별 표기를 contains로 매칭한다.
CANDIDATE_KEYWORDS = ['마곡동', '가양1동', '가양제1동', '발산1동', '발산제1동', '공항동', '방화1동', '방화제1동', '방화2동', '방화제2동', '방화3동', '방화제3동', '등촌3동', '등촌제3동', '우장산동']


def read_csv_guess(path_or_bytes, nrows=None, **kwargs):
    encodings = ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']
    last = None
    for enc in encodings:
        try:
            if isinstance(path_or_bytes, (bytes, bytearray)):
                return pd.read_csv(io.BytesIO(path_or_bytes), encoding=enc, nrows=nrows, **kwargs)
            return pd.read_csv(path_or_bytes, encoding=enc, nrows=nrows, **kwargs)
        except Exception as e:
            last = e
    raise last


def normalize_admin_name(x):
    s = str(x).strip()
    s = re.sub(r'\s+', '', s)
    s = s.replace('제1동', '1동').replace('제2동', '2동').replace('제3동', '3동').replace('제4동', '4동')
    return s


def extract_period_from_columns(cols):
    joined = ' '.join(map(str, cols))
    m = re.search(r'(20\d{2})\D*(0[1-9]|1[0-2])', joined)
    return ''.join(m.groups()) if m else ''


def inspect_store_admin_counts():
    rows = []
    frames = []
    for zp in sorted((BASE / 'admin_store_counts').glob('*.zip')):
        year = re.search(r'(20\d{2})', zp.name).group(1)
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            csv_names = [n for n in names if n.lower().endswith('.csv')]
            if not csv_names:
                rows.append({'dataset':'store_admin_counts','file':zp.name,'period':year,'status':'no_csv','rows':'','columns':''})
                continue
            name = csv_names[0]
            data = z.read(name)
            sample = read_csv_guess(data, nrows=5)
            rows.append({'dataset':'store_admin_counts','file':zp.name,'period':year,'status':'ok','rows':'pending','columns':' | '.join(map(str, sample.columns[:20]))})
            df = read_csv_guess(data)
            # Identify common columns in Seoul commercial service: 기준_년분기_코드, 행정동_코드, 행정동_코드_명, 서비스_업종_코드_명, 점포_수, 유사_업종_점포_수 등
            colmap = {c: str(c) for c in df.columns}
            dong_col = next((c for c in df.columns if '행정동' in str(c) and ('명' in str(c) or '코드_명' in str(c))), None)
            sector_col = next((c for c in df.columns if '서비스' in str(c) and '업종' in str(c) and '명' in str(c)), None)
            q_col = next((c for c in df.columns if '기준' in str(c) and ('년분기' in str(c) or '분기' in str(c))), None)
            store_col = next((c for c in df.columns if str(c).strip() in ['점포_수','점포수'] or '점포_수' in str(c)), None)
            if dong_col and sector_col and store_col:
                keep = df[[c for c in [q_col, dong_col, sector_col, store_col] if c is not None]].copy()
                keep.columns = [str(c) for c in keep.columns]
                keep['source_year'] = int(year)
                keep['admin_dong_norm'] = keep[str(dong_col)].map(normalize_admin_name)
                keep['is_candidate'] = keep['admin_dong_norm'].apply(lambda v: any(k.replace(' ','') in v for k in CANDIDATE_KEYWORDS))
                frames.append((year, keep, str(q_col) if q_col else None, str(dong_col), str(sector_col), str(store_col)))
                rows[-1]['rows'] = len(df)
            else:
                rows[-1]['status'] = 'missing_expected_columns'
                rows[-1]['rows'] = len(df)
    audit = pd.DataFrame(rows)
    audit.to_csv(OUT_LOCAL / 'temporal_source_column_audit.csv', index=False, encoding='utf-8-sig')
    if not frames:
        return None

    agg_list = []
    conv_list = []
    by_industry = []
    for year, keep, q_col, dong_col, sector_col, store_col in frames:
        store_col = str(store_col); sector_col = str(sector_col); dong_col = str(dong_col)
        keep[store_col] = pd.to_numeric(keep[store_col], errors='coerce').fillna(0)
        # Use full-year average across quarters when quarterly rows are present; also keep latest quarter as period detail.
        g = keep.groupby(['source_year','admin_dong_norm'], as_index=False)[store_col].sum()
        # If file contains all quarters, summing over all quarters overstates annual stock. Detect quarter column and average by quarter.
        if q_col and q_col in keep.columns:
            gq = keep.groupby(['source_year','admin_dong_norm', q_col], as_index=False)[store_col].sum()
            g = gq.groupby(['source_year','admin_dong_norm'], as_index=False)[store_col].mean()
            g = g.rename(columns={store_col:'avg_total_store_count'})
        else:
            g = g.rename(columns={store_col:'avg_total_store_count'})
        agg_list.append(g)
        conv_mask = keep[sector_col].astype(str).str.contains('편의점', na=False)
        conv = keep[conv_mask].copy()
        if not conv.empty:
            if q_col and q_col in conv.columns:
                cq = conv.groupby(['source_year','admin_dong_norm', q_col], as_index=False)[store_col].sum()
                cg = cq.groupby(['source_year','admin_dong_norm'], as_index=False)[store_col].mean()
            else:
                cg = conv.groupby(['source_year','admin_dong_norm'], as_index=False)[store_col].sum()
            cg = cg.rename(columns={store_col:'avg_convenience_store_count'})
            conv_list.append(cg)
        # service category top change for candidates only
        cand = keep[keep['is_candidate']].copy()
        if q_col and q_col in cand.columns:
            indq = cand.groupby(['source_year','admin_dong_norm', sector_col, q_col], as_index=False)[store_col].sum()
            ind = indq.groupby(['source_year','admin_dong_norm', sector_col], as_index=False)[store_col].mean()
        else:
            ind = cand.groupby(['source_year','admin_dong_norm', sector_col], as_index=False)[store_col].sum()
        ind = ind.rename(columns={sector_col:'service_industry', store_col:'avg_store_count'})
        by_industry.append(ind)
    total = pd.concat(agg_list, ignore_index=True)
    conv = pd.concat(conv_list, ignore_index=True) if conv_list else pd.DataFrame(columns=['source_year','admin_dong_norm','avg_convenience_store_count'])
    merged = total.merge(conv, on=['source_year','admin_dong_norm'], how='left')
    merged['avg_convenience_store_count'] = merged['avg_convenience_store_count'].fillna(0)
    merged['convenience_share_pct'] = merged['avg_convenience_store_count'] / merged['avg_total_store_count'].replace(0, pd.NA) * 100
    merged['is_candidate'] = merged['admin_dong_norm'].apply(lambda v: any(k.replace(' ','') in v for k in CANDIDATE_KEYWORDS))
    merged.to_csv(OUT_LOCAL / 'admin_store_counts_by_dong_year.csv', index=False, encoding='utf-8-sig')
    merged[merged['is_candidate']].to_csv(OUT_LOCAL / 'candidate_admin_store_counts_by_year.csv', index=False, encoding='utf-8-sig')
    pd.concat(by_industry, ignore_index=True).to_csv(OUT_LOCAL / 'candidate_store_industry_by_year.csv', index=False, encoding='utf-8-sig')
    return merged


def inspect_mois_population():
    rows = []
    hh_frames = []
    age_frames = []
    for f in sorted((BASE / 'mois_population_household').glob('*.csv')):
        period = re.search(r'(20\d{4})', f.name).group(1)
        df = read_csv_guess(f)
        rows.append({'dataset':'mois_population_household','file':f.name,'period':period,'rows':len(df),'columns':' | '.join(map(str, df.columns[:20]))})
        region_col = df.columns[0]
        data = df.copy()
        data['period'] = period
        data['year'] = int(period[:4])
        data['admin_region'] = data[region_col].astype(str)
        data['admin_dong_norm'] = data['admin_region'].str.extract(r'서울특별시\s+강서구\s+([^\(]+)', expand=False).fillna(data['admin_region']).map(normalize_admin_name)
        data = data[data['admin_region'].str.contains('서울특별시 강서구', na=False)]
        # total population and household columns typically include 총인구수 and 세대수.
        pop_col = next((c for c in data.columns if '총인구수' in str(c) and '남' not in str(c) and '여' not in str(c)), None)
        household_col = next((c for c in data.columns if '세대수' in str(c)), None)
        male_col = next((c for c in data.columns if '남자인구수' in str(c)), None)
        female_col = next((c for c in data.columns if '여자인구수' in str(c)), None)
        out = data[['period','year','admin_region','admin_dong_norm']].copy()
        for new, col in [('resident_population',pop_col),('households',household_col),('male_population',male_col),('female_population',female_col)]:
            out[new] = pd.to_numeric(data[col].astype(str).str.replace(',','', regex=False), errors='coerce') if col else pd.NA
        hh_frames.append(out)
    for f in sorted((BASE / 'mois_population_age10').glob('*.csv')):
        period = re.search(r'(20\d{4})', f.name).group(1)
        df = read_csv_guess(f)
        rows.append({'dataset':'mois_population_age10','file':f.name,'period':period,'rows':len(df),'columns':' | '.join(map(str, df.columns[:20]))})
        region_col = df.columns[0]
        data = df.copy()
        data['period'] = period
        data['year'] = int(period[:4])
        data['admin_region'] = data[region_col].astype(str)
        data = data[data['admin_region'].str.contains('서울특별시 강서구', na=False)]
        data['admin_dong_norm'] = data['admin_region'].str.extract(r'서울특별시\s+강서구\s+([^\(]+)', expand=False).fillna(data['admin_region']).map(normalize_admin_name)
        out = data[['period','year','admin_region','admin_dong_norm']].copy()
        # Use total columns by age band, avoid male/female duplicated bands.
        for band in ['0~9','10~19','20~29','30~39','40~49','50~59','60~69','70~79','80~89','90~99','100']:
            col = next((c for c in data.columns if f'_계_{band}' in str(c) or (f'_{band}' in str(c) and '_남_' not in str(c) and '_여_' not in str(c))), None)
            if col:
                safe = band.replace('~','_').replace(' ','').replace('세','')
                out[f'age_{safe}'] = pd.to_numeric(data[col].astype(str).str.replace(',','', regex=False), errors='coerce')
        # Create useful groups: 20-39, 60+, 70+
        cols20_39 = [c for c in out.columns if c in ['age_20_29','age_30_39']]
        cols60p = [c for c in out.columns if c.startswith('age_60_') or c.startswith('age_70_') or c.startswith('age_80_') or c.startswith('age_90_') or c.startswith('age_100')]
        cols70p = [c for c in out.columns if c.startswith('age_70_') or c.startswith('age_80_') or c.startswith('age_90_') or c.startswith('age_100')]
        out['pop_20_39'] = out[cols20_39].sum(axis=1) if cols20_39 else pd.NA
        out['pop_60_plus'] = out[cols60p].sum(axis=1) if cols60p else pd.NA
        out['pop_70_plus'] = out[cols70p].sum(axis=1) if cols70p else pd.NA
        age_frames.append(out)
    pd.DataFrame(rows).to_csv(OUT_LOCAL / 'mois_population_column_audit.csv', index=False, encoding='utf-8-sig')
    hh = pd.concat(hh_frames, ignore_index=True) if hh_frames else pd.DataFrame()
    age = pd.concat(age_frames, ignore_index=True) if age_frames else pd.DataFrame()
    demo = hh.merge(age[['period','admin_dong_norm','pop_20_39','pop_60_plus','pop_70_plus']], on=['period','admin_dong_norm'], how='left') if not age.empty else hh
    if not demo.empty:
        demo['is_candidate'] = demo['admin_dong_norm'].apply(lambda v: any(k.replace(' ','') in str(v) for k in CANDIDATE_KEYWORDS))
        demo['avg_household_size'] = demo['resident_population'] / demo['households'].replace(0, pd.NA)
        demo['share_20_39_pct'] = demo['pop_20_39'] / demo['resident_population'].replace(0, pd.NA) * 100
        demo['share_60_plus_pct'] = demo['pop_60_plus'] / demo['resident_population'].replace(0, pd.NA) * 100
        demo.to_csv(OUT_LOCAL / 'gangseo_demographics_by_dong_period.csv', index=False, encoding='utf-8-sig')
        demo[demo['is_candidate']].to_csv(OUT_LOCAL / 'candidate_demographics_by_period.csv', index=False, encoding='utf-8-sig')
    return demo


def inspect_living_movement():
    rows = []
    summaries = []
    for zp in sorted((BASE / 'living_movement').glob('*.zip')):
        date = re.search(r'(20\d{6})', zp.name).group(1)
        with zipfile.ZipFile(zp) as z:
            csv_names = [n for n in z.namelist() if n.lower().endswith('.csv')]
            name = csv_names[0] if csv_names else ''
            if not name:
                continue
            data = z.read(name)
            sample = read_csv_guess(data, nrows=5)
            rows.append({'dataset':'living_movement','file':zp.name,'period':date,'rows':'large','columns':' | '.join(map(str, sample.columns[:25]))})
            # Full daily OD can be large but manageable; use only rows involving Gangseo candidate names if columns available.
            df = read_csv_guess(data)
            cols = [str(c) for c in df.columns]
            # Find origin/destination admin dong name columns and movement count.
            name_cols = [c for c in df.columns if '행정동' in str(c) and ('명' in str(c) or '동' in str(c))]
            count_col = next((c for c in df.columns if '이동인구' in str(c) or '인구' == str(c).strip() or 'total' in str(c).lower()), None)
            hour_col = next((c for c in df.columns if '시간' in str(c) or '도착시간' in str(c) or '출발시간' in str(c)), None)
            purpose_col = next((c for c in df.columns if '목적' in str(c)), None)
            if count_col and name_cols:
                mask = pd.Series(False, index=df.index)
                for c in name_cols:
                    s = df[c].astype(str)
                    for k in CANDIDATE_KEYWORDS:
                        mask |= s.str.contains(k, na=False)
                sub = df.loc[mask].copy()
                sub[count_col] = pd.to_numeric(sub[count_col], errors='coerce').fillna(0)
                keys = []
                if hour_col: keys.append(hour_col)
                if purpose_col: keys.append(purpose_col)
                if keys:
                    g = sub.groupby(keys, as_index=False)[count_col].sum()
                else:
                    g = pd.DataFrame({count_col:[sub[count_col].sum()]})
                g['date'] = date
                g['row_count_filtered'] = len(sub)
                summaries.append(g.rename(columns={count_col:'movement_population'}))
    pd.DataFrame(rows).to_csv(OUT_LOCAL / 'living_movement_column_audit.csv', index=False, encoding='utf-8-sig')
    if summaries:
        lm = pd.concat(summaries, ignore_index=True)
        lm.to_csv(OUT_LOCAL / 'candidate_living_movement_summary_representative_days.csv', index=False, encoding='utf-8-sig')
        return lm
    return pd.DataFrame()


def create_combined_candidate_panel(store, demo):
    if store is None or demo is None or store.empty or demo.empty:
        return pd.DataFrame()
    # match store source_year to demographics year-end or latest 202604 for 2026 if needed. Store has 2019-2025.
    d = demo.copy()
    d = d[d['period'].str.endswith('12')].copy()
    d['source_year'] = d['year']
    s = store[store['is_candidate']].copy()
    panel = s.merge(d[['source_year','admin_dong_norm','resident_population','households','avg_household_size','pop_20_39','pop_60_plus','share_20_39_pct','share_60_plus_pct']], on=['source_year','admin_dong_norm'], how='left')
    panel['stores_per_1000_residents'] = panel['avg_total_store_count'] / panel['resident_population'].replace(0, pd.NA) * 1000
    panel['convenience_per_1000_residents'] = panel['avg_convenience_store_count'] / panel['resident_population'].replace(0, pd.NA) * 1000
    panel.to_csv(OUT_LOCAL / 'candidate_store_demographic_panel_2019_2025.csv', index=False, encoding='utf-8-sig')
    # change table from first to last available
    changes = []
    for dong, g in panel.sort_values('source_year').groupby('admin_dong_norm'):
        first = g.dropna(subset=['avg_total_store_count']).head(1)
        last = g.dropna(subset=['avg_total_store_count']).tail(1)
        if first.empty or last.empty:
            continue
        f = first.iloc[0]; l = last.iloc[0]
        def pct(a, b):
            if pd.isna(a) or pd.isna(b):
                return pd.NA
            try:
                a = float(a)
                b = float(b)
            except Exception:
                return pd.NA
            if a == 0:
                return pd.NA
            return (b - a) / a * 100
        changes.append({
            'admin_dong_norm': dong,
            'first_year': int(f['source_year']),
            'last_year': int(l['source_year']),
            'total_store_first': f['avg_total_store_count'],
            'total_store_last': l['avg_total_store_count'],
            'total_store_change_pct': pct(f['avg_total_store_count'], l['avg_total_store_count']),
            'convenience_first': f['avg_convenience_store_count'],
            'convenience_last': l['avg_convenience_store_count'],
            'convenience_change_pct': pct(f['avg_convenience_store_count'], l['avg_convenience_store_count']),
            'population_first': f['resident_population'],
            'population_last': l['resident_population'],
            'population_change_pct': pct(f['resident_population'], l['resident_population']),
            'share_20_39_last': l.get('share_20_39_pct'),
            'share_60_plus_last': l.get('share_60_plus_pct'),
            'convenience_per_1000_last': l.get('convenience_per_1000_residents'),
        })
    ch = pd.DataFrame(changes).sort_values(['total_store_change_pct','convenience_per_1000_last'], ascending=[False, False])
    ch.to_csv(OUT_LOCAL / 'candidate_change_summary_2019_2025.csv', index=False, encoding='utf-8-sig')
    return panel


def main():
    store = inspect_store_admin_counts()
    demo = inspect_mois_population()
    lm = inspect_living_movement()
    panel = create_combined_candidate_panel(store, demo)
    summary = {
        'outputs': sorted([p.name for p in OUT_LOCAL.glob('*.csv')]),
        'store_rows': 0 if store is None else int(len(store)),
        'demo_rows': 0 if demo is None else int(len(demo)),
        'living_summary_rows': int(len(lm)),
        'panel_rows': int(len(panel)),
    }
    (OUT_LOCAL / 'analysis_run_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
