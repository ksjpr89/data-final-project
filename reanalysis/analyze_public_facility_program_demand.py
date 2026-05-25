from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)

context_path = OUT / 'tableau_store_level_context_metrics.csv'
demo_path = Path('/home/ubuntu/data_final_analysis_work/reanalysis/inputs/gangseo_demographics_by_dong_period.csv')
movement_path = Path('/home/ubuntu/data_final_analysis_work/outputs/candidate_living_movement_avg_daily_direction.csv')

def read_csv_any(path, **kwargs):
    for enc in ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, **kwargs)

def minmax(s, invert=False):
    x = pd.to_numeric(s, errors='coerce')
    if x.notna().sum() == 0 or x.max() == x.min():
        out = pd.Series(0.5, index=s.index)
    else:
        out = (x - x.min()) / (x.max() - x.min())
    if invert:
        out = 1 - out
    return out.fillna(0)

context = read_csv_any(context_path)
for c in [
    'store_context_exploration_score','score_transit_access','score_public_health_need',
    'score_worker_flow_need','score_site_feasibility_pool','nearest_subway_station_distance_m',
    'nearest_gimpo_airport_axis_distance_m','nearest_magok_business_axis_distance_m',
    'medical_count_500m','other_convenience_count_500m','resident_population','households',
    'share_20_39_pct','share_60_plus_pct','inbound_to_candidate','outbound_from_candidate',
    'candidate_internal_or_between','longitude','latitude'
]:
    if c in context.columns:
        context[c] = pd.to_numeric(context[c], errors='coerce')

# 같은 건물/주소에 중복 점포명이 있는 경우 Tableau에는 모두 남기되, 최종 후보 선정용으로는 주소 단위 대표 1개만 사용한다.
# 점포명·브랜드 오기나 중복 등록이 있을 수 있으므로 source_store_id는 원자료 추적용으로 보존한다.
context['address_key'] = context['road_address'].fillna(context.get('jibun_address', '')).astype(str)
context['known_brand_priority'] = context.get('is_known_chain_brand', False).astype(str).str.lower().isin(['true','1']).astype(int)
context = context.sort_values(['address_key','known_brand_priority','store_context_exploration_score'], ascending=[True, False, False])
address_representative = context.groupby('address_key', as_index=False).head(1).copy()
address_representative = address_representative.sort_values('store_context_exploration_score', ascending=False).reset_index(drop=True)

# 2030 인구·가구 추정: 보유 행정동 인구 원자료의 2019~2026 선형추세를 2030년까지 외삽한다.
demo = read_csv_any(demo_path)
projection_rows = []
demo['admin_dong_norm'] = demo['admin_dong_norm'].astype(str).str.replace('제', '', regex=False)
for dong, g in demo.groupby('admin_dong_norm'):
    g = g.sort_values('year')
    row = {'admin_dong': dong}
    for col in ['resident_population','households','pop_20_39','pop_60_plus','share_20_39_pct','share_60_plus_pct','avg_household_size']:
        y = pd.to_numeric(g[col], errors='coerce')
        x = pd.to_numeric(g['year'], errors='coerce')
        ok = x.notna() & y.notna()
        if ok.sum() >= 2:
            slope, intercept = np.polyfit(x[ok], y[ok], 1)
            row[f'{col}_2026'] = float(y[ok].iloc[-1])
            row[f'{col}_2030_projection'] = float(slope * 2030 + intercept)
            row[f'{col}_annual_change'] = float(slope)
        elif ok.sum() == 1:
            row[f'{col}_2026'] = float(y[ok].iloc[-1])
            row[f'{col}_2030_projection'] = float(y[ok].iloc[-1])
            row[f'{col}_annual_change'] = np.nan
        else:
            row[f'{col}_2026'] = np.nan
            row[f'{col}_2030_projection'] = np.nan
            row[f'{col}_annual_change'] = np.nan
    projection_rows.append(row)
projection = pd.DataFrame(projection_rows)
projection.to_csv(OUT / 'admin_dong_population_2030_projection.csv', index=False, encoding='utf-8-sig')

stores = address_representative.copy()
stores['admin_dong'] = stores['admin_dong'].astype(str).str.replace('제', '', regex=False)
stores = stores.merge(projection, on='admin_dong', how='left')
for base_col in ['resident_population', 'households', 'avg_household_size', 'share_20_39_pct', 'share_60_plus_pct']:
    proj_col = f'{base_col}_2026'
    if base_col in stores.columns and proj_col in stores.columns:
        stores[base_col] = pd.to_numeric(stores[base_col], errors='coerce').fillna(pd.to_numeric(stores[proj_col], errors='coerce'))
    elif proj_col in stores.columns:
        stores[base_col] = pd.to_numeric(stores[proj_col], errors='coerce')

# 프로그램별 수요 점수: 편의점 신규 출점이 아니라 위층 공공시설 프로그램 선택을 위한 점수이다.
stores['component_young_worker'] = (
    0.30 * minmax(stores['inbound_to_candidate']) +
    0.20 * minmax(stores['share_20_39_pct']) +
    0.20 * minmax(stores['nearest_magok_business_axis_distance_m'], invert=True) +
    0.20 * minmax(stores['score_transit_access']) +
    0.10 * minmax(stores['other_convenience_count_500m'])
)
stores['component_health_dolbom'] = (
    0.25 * minmax(stores['share_60_plus_pct']) +
    0.25 * minmax(stores['share_60_plus_pct_2030_projection']) +
    0.20 * minmax(stores['medical_count_500m']) +
    0.15 * minmax(stores['resident_population']) +
    0.15 * minmax(stores['score_transit_access'])
)
stores['component_airport_mobility_support'] = (
    0.35 * minmax(stores['nearest_gimpo_airport_axis_distance_m'], invert=True) +
    0.25 * minmax(stores['inbound_to_candidate']) +
    0.20 * minmax(stores['score_transit_access']) +
    0.10 * minmax(stores['other_convenience_count_500m']) +
    0.10 * minmax(stores['nearest_subway_station_distance_m'], invert=True)
)
stores['component_general_life_admin'] = (
    0.25 * minmax(stores['resident_population']) +
    0.20 * minmax(stores['households']) +
    0.20 * minmax(stores['candidate_internal_or_between']) +
    0.20 * minmax(stores['score_transit_access']) +
    0.15 * minmax(stores['other_convenience_count_500m'])
)

program_cols = [
    'component_young_worker', 'component_health_dolbom',
    'component_airport_mobility_support', 'component_general_life_admin'
]
program_names = {
    'component_young_worker': '청년·직장인 생활지원형 공공시설',
    'component_health_dolbom': '생활건강·돌봄 상담형 공공시설',
    'component_airport_mobility_support': '공항권 이동노동자·외국인 생활지원형 공공시설',
    'component_general_life_admin': '생활민원·커뮤니티 거점형 공공시설'
}
stores['best_program_score_column'] = stores[program_cols].idxmax(axis=1)
stores['recommended_public_facility_program'] = stores['best_program_score_column'].map(program_names)
stores['recommended_program_score'] = stores[program_cols].max(axis=1)
stores['evidence_summary'] = stores.apply(
    lambda r: (
        f"가장 가까운 지하철 {r.get('nearest_subway_station_name','')} {r.get('nearest_subway_station_distance_m', np.nan):.1f}m, "
        f"500m 병의원 {r.get('medical_count_500m', np.nan):.0f}개, "
        f"500m 내 편의점 {r.get('other_convenience_count_500m', np.nan):.0f}개, "
        f"행정동 유입 생활이동 평균 {r.get('inbound_to_candidate', np.nan):.0f}명, "
        f"20~39세 비중 {r.get('share_20_39_pct', np.nan):.1f}%, 60세 이상 비중 {r.get('share_60_plus_pct', np.nan):.1f}%"
    ), axis=1
)

# 점수만으로 한 동에 쏠리지 않도록 프로그램별·권역별 후보를 동시에 뽑는다.
stores = stores.sort_values('recommended_program_score', ascending=False).reset_index(drop=True)
stores['overall_program_rank'] = np.arange(1, len(stores) + 1)

store_score_cols = [
    'candidate_store_id','source_store_id','store_name','brand','admin_dong','road_address','jibun_address',
    'longitude','latitude','recommended_public_facility_program','recommended_program_score',
    'component_young_worker','component_health_dolbom','component_airport_mobility_support','component_general_life_admin',
    'store_context_exploration_score','nearest_subway_station_name','nearest_subway_station_distance_m',
    'subway_station_count_500m','subway_station_count_800m','nearest_medical_name','nearest_medical_distance_m',
    'medical_count_500m','medical_count_800m','other_convenience_count_250m','other_convenience_count_500m',
    'nearest_other_convenience_distance_m','nearest_magok_business_axis_name','nearest_magok_business_axis_distance_m',
    'nearest_gimpo_airport_axis_name','nearest_gimpo_airport_axis_distance_m','resident_population','households',
    'share_20_39_pct','share_60_plus_pct','share_20_39_pct_2030_projection','share_60_plus_pct_2030_projection',
    'inbound_to_candidate','outbound_from_candidate','candidate_internal_or_between','evidence_summary','overall_program_rank'
]
store_score_cols = [c for c in store_score_cols if c in stores.columns]
stores[store_score_cols].to_csv(OUT / 'tableau_store_public_facility_program_scores.csv', index=False, encoding='utf-8-sig')

shortlist_parts = []
for col, name in program_names.items():
    tmp = stores.sort_values(col, ascending=False).head(5).copy()
    tmp['shortlist_basis'] = name
    tmp['shortlist_program_component_score'] = tmp[col]
    shortlist_parts.append(tmp)
shortlist = pd.concat(shortlist_parts, ignore_index=True)
shortlist = shortlist.sort_values(['shortlist_basis','shortlist_program_component_score'], ascending=[True, False])
shortlist = shortlist.drop_duplicates(subset=['address_key','shortlist_basis'])
shortlist_cols = ['shortlist_basis','shortlist_program_component_score'] + store_score_cols
shortlist_cols = [c for c in shortlist_cols if c in shortlist.columns]
shortlist[shortlist_cols].to_csv(OUT / 'final_public_facility_site_shortlist_by_program.csv', index=False, encoding='utf-8-sig')

# PPT용 핵심 후보 8개: 종합 상위와 프로그램별 다양성을 섞되 중복 주소 제거.
core = pd.concat([
    stores.head(8),
    *[stores.sort_values(col, ascending=False).head(3) for col in program_cols]
], ignore_index=True).drop_duplicates(subset=['address_key']).head(12)
core[store_score_cols].to_csv(OUT / 'ppt_core_store_candidates_with_programs.csv', index=False, encoding='utf-8-sig')

# 분석 한계와 추가 확인 필요 항목을 데이터 산출물로 남긴다.
gaps = pd.DataFrame([
    {'item':'편의점 위층 실제 활용 가능 여부','status':'추가 확인 필요','reason':'상가업소 원자료에는 건물 층수, 공실, 임대 가능 면적, 소유관계가 없음','suggested_check':'네이버지도/카카오맵 로드뷰, 건축물대장, 현장확인으로 2층 이상 상가·공실 여부 확인'},
    {'item':'점포별 시간대 유동인구','status':'추가 확인 필요','reason':'현재 보유 생활이동 데이터는 행정동 평균 방향별 집계이며 점포 반경·시간대별 유동인구가 아님','suggested_check':'서울 생활이동 시간대 원자료 또는 카드/통신 유동인구 자료를 Tableau에 추가'},
    {'item':'기존 공공시설 공급 부족 여부','status':'추가 확인 필요','reason':'현재 산식은 병의원·역세권·생활이동·인구로 수요를 추정하나 주민센터·도서관·복지관 등 공급 위치를 아직 결합하지 않음','suggested_check':'공공시설 POI를 추가해 후보 반경 내 중복 공급 여부 검증'},
    {'item':'2030 예측 정확도','status':'보조 근거로만 사용','reason':'2019~2026 행정동 인구 추세의 단순 선형 외삽이므로 정책·개발변수 미반영','suggested_check':'서울시 장래인구 또는 도시계획 자료와 비교'}
])
gaps.to_csv(OUT / 'public_facility_reanalysis_data_gaps_to_check.csv', index=False, encoding='utf-8-sig')

print('완료: 공공시설 프로그램 수요 점수 및 후보 편의점 shortlist 생성')
print('주소 단위 후보 수:', len(stores))
print('핵심 후보 상위 8개')
print(stores[store_score_cols].head(8).to_string(index=False))
