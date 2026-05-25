from pathlib import Path
import math
import pandas as pd
import numpy as np

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)

stores_path = OUT / 'tableau_convenience_stores_gangseo.csv'
hospital_path = Path('/home/ubuntu/data_final_analysis_work/expanded_inputs/seoul_hospital_clinic_locations_20260508.csv')
subway_path = Path('/home/ubuntu/Downloads/서울시 역사마스터 정보.csv')
demo_path = Path('/home/ubuntu/data_final_analysis_work/outputs/candidate_demographics_by_period.csv')
movement_path = Path('/home/ubuntu/data_final_analysis_work/outputs/candidate_living_movement_avg_daily_direction.csv')
admin_score_path = Path('/home/ubuntu/data_final_analysis_work/outputs/expanded_multi_indicator_analysis_20260522/candidate_final_ranking.csv')


def read_csv_any(path, **kwargs):
    for enc in ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, **kwargs)


def haversine_np(lat1, lon1, lat2, lon2):
    r = 6371000.0
    lat1 = np.radians(lat1.astype(float))
    lon1 = np.radians(lon1.astype(float))
    lat2 = np.radians(lat2.astype(float))
    lon2 = np.radians(lon2.astype(float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def nearest_and_counts(stores, poi, lat_col, lon_col, name_col, prefix, radii=(300, 500, 800, 1000)):
    result = stores[['candidate_store_id']].copy()
    if poi.empty:
        result[f'nearest_{prefix}_name'] = ''
        result[f'nearest_{prefix}_distance_m'] = np.nan
        for radius in radii:
            result[f'{prefix}_count_{radius}m'] = 0
        return result

    store_lat = stores['latitude'].to_numpy()
    store_lon = stores['longitude'].to_numpy()
    poi_lat = poi[lat_col].to_numpy()
    poi_lon = poi[lon_col].to_numpy()
    n = len(stores)
    nearest_dist = np.full(n, np.inf)
    nearest_idx = np.full(n, -1, dtype=int)
    counts = {r: np.zeros(n, dtype=int) for r in radii}

    # POI 수가 크므로 점포별로 계산하되 전체 551개라 충분히 빠르다.
    for i in range(n):
        d = haversine_np(np.full(len(poi), store_lat[i]), np.full(len(poi), store_lon[i]), poi_lat, poi_lon)
        j = int(np.argmin(d))
        nearest_dist[i] = float(d[j])
        nearest_idx[i] = j
        for r in radii:
            counts[r][i] = int((d <= r).sum())

    result[f'nearest_{prefix}_name'] = [str(poi.iloc[j][name_col]) if j >= 0 else '' for j in nearest_idx]
    result[f'nearest_{prefix}_distance_m'] = np.round(nearest_dist, 1)
    for r in radii:
        result[f'{prefix}_count_{r}m'] = counts[r]
    return result


stores = read_csv_any(stores_path)
stores['latitude'] = pd.to_numeric(stores['latitude'], errors='coerce')
stores['longitude'] = pd.to_numeric(stores['longitude'], errors='coerce')
stores = stores.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)

# 편의점 간 밀도: 자기 자신은 제외한다.
n = len(stores)
other_counts = {100: [], 250: [], 500: [], 800: []}
nearest_other_dist = []
for i, row in stores.iterrows():
    d = haversine_np(np.full(n, row['latitude']), np.full(n, row['longitude']), stores['latitude'].to_numpy(), stores['longitude'].to_numpy())
    d[i] = np.inf
    nearest_other_dist.append(float(np.min(d)))
    for r in other_counts:
        other_counts[r].append(int((d <= r).sum()))

context = stores.copy()
known_brand_set = {'GS25', 'CU', '세븐일레븐', '이마트24', '미니스톱'}
context['is_known_chain_brand'] = context['brand'].isin(known_brand_set)
context['nearest_other_convenience_distance_m'] = np.round(nearest_other_dist, 1)
for r, vals in other_counts.items():
    context[f'other_convenience_count_{r}m'] = vals

# 병원·의원 위치: 강서구 주소만 사용한다.
hospitals = read_csv_any(hospital_path)
addr_col = '주소'
name_col = '기관명'
hospitals['병원경도'] = pd.to_numeric(hospitals['병원경도'], errors='coerce')
hospitals['병원위도'] = pd.to_numeric(hospitals['병원위도'], errors='coerce')
hospitals_gs = hospitals[
    hospitals[addr_col].astype(str).str.contains('강서구', na=False)
].dropna(subset=['병원경도', '병원위도']).copy()
health_metrics = nearest_and_counts(context, hospitals_gs, '병원위도', '병원경도', name_col, 'medical', radii=(300, 500, 800, 1000))
context = context.merge(health_metrics, on='candidate_store_id', how='left')

# 지하철역 좌표: 서울시 역사마스터 정보에서 강서구 주변 관련 역사만 필터링한다.
subway = read_csv_any(subway_path)
subway.columns = [str(c).replace('\ufeff', '').strip() for c in subway.columns]
# 서울 열린데이터광장 파일은 컬럼명이 역사_ID, 역사명, 호선, 위도, 경도 구조다.
subway['위도'] = pd.to_numeric(subway['위도'], errors='coerce')
subway['경도'] = pd.to_numeric(subway['경도'], errors='coerce')
subway = subway.dropna(subset=['위도', '경도']).copy()
# 강서구 및 인접 접근권. 좌표 범위는 강서구와 바로 주변 역사까지 포함한다.
subway_gs = subway[(subway['위도'].between(37.50, 37.62)) & (subway['경도'].between(126.75, 126.91))].copy()
subway_gs['station_line_name'] = subway_gs['역사명'].astype(str) + '(' + subway_gs['호선'].astype(str) + ')'
subway_metrics = nearest_and_counts(context, subway_gs, '위도', '경도', 'station_line_name', 'subway_station', radii=(300, 500, 800, 1000))
context = context.merge(subway_metrics, on='candidate_store_id', how='left')

# 마곡 업무권과 김포공항 접근성: 공개 지하철역 좌표의 대표 역사까지 최단거리로 산출한다.
magok_stations = subway[subway['역사명'].astype(str).isin(['마곡', '마곡나루', '발산'])].copy()
airport_stations = subway[subway['역사명'].astype(str).isin(['김포공항'])].copy()
for label, poi in [('magok_business_axis', magok_stations), ('gimpo_airport_axis', airport_stations)]:
    tmp = nearest_and_counts(context, poi.assign(station_line_name=poi['역사명'].astype(str) + '(' + poi['호선'].astype(str) + ')'), '위도', '경도', 'station_line_name', label, radii=(500, 1000, 1500, 2000))
    keep = ['candidate_store_id', f'nearest_{label}_name', f'nearest_{label}_distance_m'] + [c for c in tmp.columns if c.startswith(f'{label}_count_')]
    context = context.merge(tmp[keep], on='candidate_store_id', how='left')

# 행정동 단위 보조 지표 결합: 가능한 경우만 붙인다.
demo = read_csv_any(demo_path)
latest_demo = demo.sort_values('period').groupby('admin_dong_norm').tail(1)[[
    'admin_dong_norm', 'resident_population', 'households', 'avg_household_size',
    'share_20_39_pct', 'share_60_plus_pct'
]].rename(columns={'admin_dong_norm': 'admin_dong'})
context = context.merge(latest_demo, on='admin_dong', how='left')

movement = read_csv_any(movement_path)
mov_pivot = movement.pivot_table(index='candidate_dong', columns='direction', values='movement_population', aggfunc='mean').reset_index()
mov_pivot = mov_pivot.rename(columns={'candidate_dong': 'admin_dong'})
context = context.merge(mov_pivot, on='admin_dong', how='left')

admin_scores = read_csv_any(admin_score_path)
if 'admin_dong_norm' in admin_scores.columns:
    admin_scores = admin_scores.rename(columns={'admin_dong_norm': 'admin_dong'})
score_cols = [c for c in admin_scores.columns if c in ['admin_dong', 'final_score', 'final_rank', 'demand_score', 'growth_score', 'competition_score', 'accessibility_score', 'anchor_score']]
context = context.merge(admin_scores[score_cols], on='admin_dong', how='left')

# 점포 단위 맥락 점수. 이는 최종 공공시설 유형 결정 전 후보 점포를 좁히기 위한 탐색 점수이다.
def minmax(s, invert=False):
    x = pd.to_numeric(s, errors='coerce')
    if x.notna().sum() == 0 or x.max() == x.min():
        out = pd.Series(0.5, index=s.index)
    else:
        out = (x - x.min()) / (x.max() - x.min())
    if invert:
        out = 1 - out
    return out.fillna(0)

context['score_transit_access'] = (
    0.55 * minmax(context['nearest_subway_station_distance_m'], invert=True) +
    0.45 * minmax(context['subway_station_count_800m'])
)
context['score_public_health_need'] = (
    0.40 * minmax(context['medical_count_500m']) +
    0.30 * minmax(context['share_60_plus_pct']) +
    0.30 * minmax(context['resident_population'])
)
context['score_worker_flow_need'] = (
    0.45 * minmax(context.get('inbound_to_candidate', pd.Series(index=context.index, dtype=float))) +
    0.35 * minmax(context['nearest_magok_business_axis_distance_m'], invert=True) +
    0.20 * minmax(context['nearest_gimpo_airport_axis_distance_m'], invert=True)
)
context['score_site_feasibility_pool'] = (
    0.35 * minmax(context['other_convenience_count_500m']) +
    0.35 * minmax(context['nearest_other_convenience_distance_m'], invert=True) +
    0.30 * minmax(context.get('final_score', pd.Series(index=context.index, dtype=float)))
)
context['store_context_exploration_score'] = (
    0.25 * context['score_transit_access'] +
    0.25 * context['score_public_health_need'] +
    0.25 * context['score_worker_flow_need'] +
    0.25 * context['score_site_feasibility_pool']
)

context['candidate_public_facility_direction'] = np.select(
    [
        (context['score_public_health_need'] >= context['score_worker_flow_need']) & (context['share_60_plus_pct'].fillna(0) >= 20),
        (context['score_worker_flow_need'] > context['score_public_health_need']) & (context['nearest_magok_business_axis_distance_m'].fillna(999999) <= 1500),
        (context['nearest_gimpo_airport_axis_distance_m'].fillna(999999) <= 1500),
    ],
    ['생활건강·돌봄 상담형 공공시설', '청년·직장인 생활지원/쉼터형 공공시설', '공항권 이동노동자·외국인 생활지원형 공공시설'],
    default='복합 생활민원·커뮤니티 거점형 공공시설'
)

# Tableau용 컬럼 순서 정리
front_cols = [
    'candidate_store_id', 'store_name', 'brand', 'admin_dong', 'road_address', 'jibun_address',
    'longitude', 'latitude', 'candidate_public_facility_direction', 'store_context_exploration_score',
    'score_transit_access', 'score_public_health_need', 'score_worker_flow_need', 'score_site_feasibility_pool',
    'nearest_subway_station_name', 'nearest_subway_station_distance_m', 'subway_station_count_500m', 'subway_station_count_800m',
    'nearest_medical_name', 'nearest_medical_distance_m', 'medical_count_500m', 'medical_count_800m',
    'other_convenience_count_250m', 'other_convenience_count_500m', 'nearest_other_convenience_distance_m',
    'nearest_magok_business_axis_name', 'nearest_magok_business_axis_distance_m',
    'nearest_gimpo_airport_axis_name', 'nearest_gimpo_airport_axis_distance_m',
    'resident_population', 'households', 'avg_household_size', 'share_20_39_pct', 'share_60_plus_pct',
    'inbound_to_candidate', 'outbound_from_candidate', 'candidate_internal_or_between',
    'final_score', 'final_rank'
]
front_cols = [c for c in front_cols if c in context.columns]
other_cols = [c for c in context.columns if c not in front_cols]
context = context[front_cols + other_cols]

context = context.sort_values('store_context_exploration_score', ascending=False)
context.to_csv(OUT / 'tableau_store_level_context_metrics.csv', index=False, encoding='utf-8-sig')
context.head(50).to_csv(OUT / 'top50_store_level_context_candidates.csv', index=False, encoding='utf-8-sig')
known_context = context[context['is_known_chain_brand']].copy()
known_context.head(50).to_csv(OUT / 'top50_known_chain_store_level_context_candidates.csv', index=False, encoding='utf-8-sig')

admin_summary = context.groupby('admin_dong').agg(
    store_count=('candidate_store_id', 'count'),
    avg_context_score=('store_context_exploration_score', 'mean'),
    max_context_score=('store_context_exploration_score', 'max'),
    avg_other_convenience_500m=('other_convenience_count_500m', 'mean'),
    avg_medical_500m=('medical_count_500m', 'mean'),
    avg_subway_distance_m=('nearest_subway_station_distance_m', 'mean'),
    avg_magok_distance_m=('nearest_magok_business_axis_distance_m', 'mean'),
    avg_airport_distance_m=('nearest_gimpo_airport_axis_distance_m', 'mean'),
).reset_index().sort_values('max_context_score', ascending=False)
admin_summary.to_csv(OUT / 'store_context_summary_by_admin_dong.csv', index=False, encoding='utf-8-sig')

quality = pd.DataFrame({
    'check_item': [
        'input_store_count', 'output_store_count', 'hospital_gangseo_count', 'subway_near_gangseo_count',
        'missing_store_coordinates', 'missing_nearest_subway', 'missing_nearest_medical'
    ],
    'value': [
        len(stores), len(context), len(hospitals_gs), len(subway_gs),
        int(stores[['latitude', 'longitude']].isna().any(axis=1).sum()),
        int(context['nearest_subway_station_distance_m'].isna().sum()),
        int(context['nearest_medical_distance_m'].isna().sum()),
    ]
})
brand_quality = context.groupby(['brand', 'is_known_chain_brand']).agg(store_count=('candidate_store_id', 'count')).reset_index().sort_values('store_count', ascending=False)
brand_quality.to_csv(OUT / 'store_brand_quality_summary.csv', index=False, encoding='utf-8-sig')
quality.to_csv(OUT / 'store_context_quality_checks.csv', index=False, encoding='utf-8-sig')

print('완료: 점포 단위 컨텍스트 지표 생성')
print('편의점 수:', len(context))
print('강서구 병원 수:', len(hospitals_gs))
print('강서구 주변 지하철역 수:', len(subway_gs))
print('상위 10개 후보:')
print(context[['candidate_store_id', 'store_name', 'admin_dong', 'road_address', 'candidate_public_facility_direction', 'store_context_exploration_score', 'nearest_subway_station_name', 'nearest_subway_station_distance_m', 'medical_count_500m', 'other_convenience_count_500m']].head(10).to_string(index=False))
