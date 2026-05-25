from pathlib import Path
import json
import time
import requests
import pandas as pd
from requests.exceptions import RequestException

BASE = 'https://www.airport.co.kr'
URL = BASE + '/www/ajaxf/frFlightStatsSvc/airPortYearList.do'
REFERER = BASE + '/www/cms/frFlightStatsCon/airportYearStats.do?MENU_ID=1250'
OUT_DIR = Path('/home/ubuntu/data_final_analysis_work/reanalysis/outputs')
OUT_DIR.mkdir(parents=True, exist_ok=True)

AIRPORTS = {
    'GMP': '김포', 'PUS': '김해', 'CJU': '제주', 'CJJ': '청주', 'TAE': '대구',
    'MWX': '무안', 'YNY': '양양', 'KWJ': '광주', 'USN': '울산', 'RSU': '여수',
    'KPO': '포항경주', 'HIN': '사천', 'KUV': '군산', 'WJU': '원주', 'ICN': '인천'
}
LINE_TYPES = {'total': '', 'domestic': '0', 'international': '1'}
YEARS = range(2016, 2026)  # 과제에는 최근 5~10년 추이가 필요하므로 2016~2025 완전연도만 우선 수집한다.

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': BASE,
    'Referer': REFERER,
})
# establish cookies; KAC 서버가 간헐적으로 TLS/응답 지연을 보이므로 실패해도 Ajax 직접 호출을 시도한다.
try:
    session.get(REFERER, timeout=15)
except RequestException as e:
    print(f'initial referer request skipped after {type(e).__name__}', flush=True)

def to_int(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    s = str(x).replace(',', '').strip()
    if s in ('', '-', 'None', 'null'):
        return None
    try:
        return int(float(s))
    except ValueError:
        return None

def fetch(year, line_type):
    data = {
        'MENU_ID': '1250',
        'pageNo': '1',
        'PRE_YY': str(year - 1),
        'ST_YY': str(year),
        'ST_MM': '01',
        'EN_MM': '12',
        'AIRPORT_CHK': list(AIRPORTS.keys()),
        'LINE_TYPE': line_type,
        'RAGUL_TYPE': '',
        'USE_TYPE': '',
        'PASS_TYPE': '',
        'CAGO_TYPE': '',
    }
    last_error = None
    for attempt in range(1, 5):
        try:
            r = session.post(URL, data=data, timeout=20)
            r.raise_for_status()
            try:
                return r.json()
            except Exception as e:
                raise RuntimeError(f'JSON parse failed for {year=} {line_type=}: {r.text[:500]}') from e
        except RequestException as e:
            last_error = e
            print(f'  retry {attempt}/4 after request error: {type(e).__name__}', flush=True)
            time.sleep(1.5 * attempt)
    raise last_error

raw = {}
rows = []
for year in YEARS:
    for line_name, line_value in LINE_TYPES.items():
        print(f'fetching {year} {line_name}', flush=True)
        payload = fetch(year, line_value)
        raw[f'{year}_{line_name}'] = payload
        if isinstance(payload, dict) and isinstance(payload.get('data'), list):
            payload_rows = payload['data']
        elif isinstance(payload, list):
            payload_rows = payload
        else:
            print('Unexpected payload', year, line_name, type(payload), str(payload)[:300])
            continue
        for item in payload_rows:
            # 첫 행 또는 합계 행은 공항 코드/명 구조가 다를 수 있어 가능한 한 원자료 필드를 보존한다.
            airport_code = item.get('A_AIRPORT') or item.get('AIRPORT') or item.get('AP_CD') or item.get('A_AP')
            airport_name = item.get('KOR_N') or item.get('KOR_NM') or item.get('AIRPORT_NM')
            if not airport_code and airport_name not in AIRPORTS.values() and airport_name not in ('합계', '계', '전체'):
                # Keep only interpretable rows.
                pass
            fp = to_int(item.get('A_FP')) or 0      # 유임여객
            ts = to_int(item.get('A_TS')) or 0      # 환승여객
            np = to_int(item.get('A_NP')) or 0      # 무임여객
            pre_fp = to_int(item.get('PRE_FP')) or 0
            pre_ts = to_int(item.get('PRE_TS')) or 0
            pre_np = to_int(item.get('PRE_NP')) or 0
            rows.append({
                'year': year,
                'line_type': line_name,
                'airport_code': airport_code,
                'airport_name': airport_name,
                'flight_count_current': to_int(item.get('A_OC')),
                'flight_count_previous': to_int(item.get('PRE_OC')),
                'paid_passenger_current': fp,
                'transfer_passenger_current': ts,
                'free_passenger_current': np,
                'passenger_total_current': fp + ts + np,
                'paid_passenger_previous': pre_fp,
                'transfer_passenger_previous': pre_ts,
                'free_passenger_previous': pre_np,
                'passenger_total_previous': pre_fp + pre_ts + pre_np,
                'cargo_current': to_int(item.get('A_CG')),
                'cargo_previous': to_int(item.get('PRE_CG')),
                'raw_keys': '|'.join(sorted(item.keys())),
            })
        # 요청 사이를 조금 띄워 KAC 서버 응답 지연을 완화한다.
        time.sleep(0.2)

raw_path = OUT_DIR / 'kac_airport_year_stats_raw_2016_2025.json'
raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')

df = pd.DataFrame(rows)
# Drop duplicated/blank non-airport rows only after inspection: retain rows with code or 합계-like names.
df.to_csv(OUT_DIR / 'kac_airport_year_stats_tidy_2016_2025.csv', index=False, encoding='utf-8-sig')

# 김포공항 및 전체 합산 요약
known_codes = set(AIRPORTS.keys())
airport_rows = df[df['airport_code'].isin(known_codes)].copy()
summary = []
for year in YEARS:
    total_airports = airport_rows[(airport_rows.year == year) & (airport_rows.line_type == 'total')]
    domestic_airports = airport_rows[(airport_rows.year == year) & (airport_rows.line_type == 'domestic')]
    international_airports = airport_rows[(airport_rows.year == year) & (airport_rows.line_type == 'international')]
    gmp_total = total_airports[total_airports.airport_code == 'GMP']
    gmp_dom = domestic_airports[domestic_airports.airport_code == 'GMP']
    gmp_int = international_airports[international_airports.airport_code == 'GMP']
    row = {
        'year': year,
        'gimpo_passenger_total': int(gmp_total['passenger_total_current'].sum()),
        'gimpo_domestic_passenger': int(gmp_dom['passenger_total_current'].sum()),
        'gimpo_international_passenger': int(gmp_int['passenger_total_current'].sum()),
        'kac_airports_passenger_total': int(total_airports['passenger_total_current'].sum()),
        'kac_airports_domestic_passenger': int(domestic_airports['passenger_total_current'].sum()),
        'kac_airports_international_passenger': int(international_airports['passenger_total_current'].sum()),
    }
    row['gimpo_share_of_kac_airports_total_pct'] = (row['gimpo_passenger_total'] / row['kac_airports_passenger_total'] * 100) if row['kac_airports_passenger_total'] else None
    row['gimpo_domestic_ratio_pct'] = (row['gimpo_domestic_passenger'] / row['gimpo_passenger_total'] * 100) if row['gimpo_passenger_total'] else None
    row['gimpo_international_ratio_pct'] = (row['gimpo_international_passenger'] / row['gimpo_passenger_total'] * 100) if row['gimpo_passenger_total'] else None
    summary.append(row)
summary_df = pd.DataFrame(summary)
summary_df.to_csv(OUT_DIR / 'kac_gimpo_airport_passenger_summary_2016_2025.csv', index=False, encoding='utf-8-sig')

recent = summary_df[summary_df.year >= 2019].copy()
if not recent.empty:
    base_2019 = summary_df.loc[summary_df.year == 2019, 'gimpo_passenger_total'].iloc[0]
    latest = summary_df.loc[summary_df.year == 2025, 'gimpo_passenger_total'].iloc[0]
    change_2019_2025 = (latest / base_2019 - 1) * 100 if base_2019 else None
else:
    change_2019_2025 = None

md = []
md.append('# 김포공항 연도별 여객 통계 수집 결과\n')
md.append('자료원: 한국공항공사 항공통계 페이지의 공항별 전년대비 통계 Ajax 엔드포인트(`/www/ajaxf/frFlightStatsSvc/airPortYearList.do`). 조회 조건은 2006~2025년 각 연도 01~12월, 공항 구분은 한국공항공사 페이지에 노출된 공항 코드 전체, 노선 구분은 전체·국내선·국제선이다.\n')
md.append(f'- 원자료 JSON: `{raw_path}`\n')
md.append('- 정제 CSV: `kac_airport_year_stats_tidy_2016_2025.csv`\n')
md.append('- 김포 요약 CSV: `kac_gimpo_airport_passenger_summary_2016_2025.csv`\n')
md.append('\n## 김포공항 최근 10년 요약\n')
show = summary_df[summary_df.year >= 2016][['year','gimpo_passenger_total','gimpo_domestic_passenger','gimpo_international_passenger','gimpo_share_of_kac_airports_total_pct','gimpo_domestic_ratio_pct']].copy()
for col in ['gimpo_share_of_kac_airports_total_pct','gimpo_domestic_ratio_pct']:
    show[col] = show[col].round(2)
md.append(show.to_markdown(index=False))
md.append('\n\n## 핵심 수치\n')
for y in [2019, 2020, 2021, 2022, 2023, 2024, 2025]:
    r = summary_df[summary_df.year == y]
    if not r.empty:
        rr = r.iloc[0]
        md.append(f"- {y}년 김포공항 총여객: {rr['gimpo_passenger_total']:,}명, 국내선 {rr['gimpo_domestic_passenger']:,}명({rr['gimpo_domestic_ratio_pct']:.2f}%), 국제선 {rr['gimpo_international_passenger']:,}명({rr['gimpo_international_ratio_pct']:.2f}%).")
if change_2019_2025 is not None:
    md.append(f"- 2019년 대비 2025년 김포공항 총여객 변화율: {change_2019_2025:.2f}%.")

(OUT_DIR / 'kac_gimpo_airport_passenger_findings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('saved', OUT_DIR / 'kac_gimpo_airport_passenger_summary_2016_2025.csv')
print(summary_df.tail())
