from pathlib import Path
import math
import pandas as pd
import numpy as np

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)
FACILITY_CSV = Path('/home/ubuntu/Downloads/서울시 시설물 정보.csv')
CANDIDATE_CSV = OUT / 'ppt_core_store_candidates_with_programs.csv'


def haversine_m(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371000 * c


def classify_facility(name: str, use_code: str, addr: str) -> str:
    s = f'{name} {use_code} {addr}'
    if any(k in s for k in ['도서관', '작은도서관', '북카페']):
        return '도서관·학습'
    if any(k in s for k in ['주민센터', '동주민센터', '구청', '보건소', '보건지소', '치안센터', '파출소', '119', '소방']):
        return '행정·공공서비스'
    if any(k in s for k in ['복지관', '노인', '경로당', '장애인', '청소년', '아동', '가족센터', '돌봄', '어르신']):
        return '복지·돌봄'
    if any(k in s for k in ['문화', '체육', '센터', '회관', '박물관', '미술관']):
        return '문화·체육·커뮤니티'
    if any(k in s for k in ['공원', '광장', '녹지']):
        return '공원·오픈스페이스'
    if any(k in s for k in ['병원', '의원', '한의원', '치과', '약국', '의료', '클리닉']):
        return '의료'
    return '기타시설'


def program_target_categories(program: str):
    if '청년' in program or '직장인' in program:
        return ['도서관·학습', '행정·공공서비스', '문화·체육·커뮤니티']
    if '돌봄' in program or '건강' in program:
        return ['복지·돌봄', '행정·공공서비스', '의료']
    if '공항권' in program or '이동노동자' in program or '외국인' in program:
        return ['행정·공공서비스', '복지·돌봄', '문화·체육·커뮤니티']
    return ['행정·공공서비스', '복지·돌봄', '도서관·학습']


def main():
    candidates = pd.read_csv(CANDIDATE_CSV, encoding='utf-8-sig')
    facilities = pd.read_csv(FACILITY_CSV, encoding='cp949')
    facilities = facilities.rename(columns={
        '시설명': 'facility_name', '위도': 'latitude', '경도': 'longitude',
        '시설용도분류': 'facility_use_code', '소재지 도로명주소': 'road_address',
        '소재지 지번주소': 'jibun_address', '데이터 기준일자': 'data_reference_date'
    })
    facilities['road_address'] = facilities['road_address'].fillna('')
    facilities['jibun_address'] = facilities['jibun_address'].fillna('')
    facilities['facility_name'] = facilities['facility_name'].fillna('')
    facilities['facility_use_code'] = facilities['facility_use_code'].fillna('')
    gangseo = facilities[
        facilities['road_address'].str.contains('강서구', na=False) |
        facilities['jibun_address'].str.contains('강서구', na=False)
    ].copy()
    gangseo = gangseo.dropna(subset=['latitude', 'longitude'])
    gangseo['facility_category'] = [classify_facility(n, u, a) for n, u, a in zip(gangseo['facility_name'], gangseo['facility_use_code'], gangseo['road_address'] + ' ' + gangseo['jibun_address'])]
    keep_cols = ['facility_name', 'facility_category', 'facility_use_code', 'road_address', 'jibun_address', 'longitude', 'latitude', 'data_reference_date']
    gangseo[keep_cols].to_csv(OUT / 'tableau_existing_public_facilities_gangseo.csv', index=False, encoding='utf-8-sig')

    detail_rows = []
    summary_rows = []
    for _, c in candidates.iterrows():
        d = haversine_m(c['longitude'], c['latitude'], gangseo['longitude'].values, gangseo['latitude'].values)
        near = gangseo.copy()
        near['distance_m'] = d
        near = near.sort_values('distance_m')
        target_cats = program_target_categories(str(c['recommended_public_facility_program']))
        near_target = near[near['facility_category'].isin(target_cats)].copy()
        for _, f in near.head(20).iterrows():
            detail_rows.append({
                'candidate_store_id': c['candidate_store_id'],
                'store_name': c['store_name'],
                'store_road_address': c['road_address'],
                'recommended_public_facility_program': c['recommended_public_facility_program'],
                'facility_name': f['facility_name'],
                'facility_category': f['facility_category'],
                'facility_road_address': f['road_address'],
                'facility_longitude': f['longitude'],
                'facility_latitude': f['latitude'],
                'distance_m': round(float(f['distance_m']), 1),
                'is_target_category_for_program': f['facility_category'] in target_cats,
                'source': '서울 열린데이터광장 서울시 시설물 정보, 2023-04-21 갱신'
            })
        counts_300 = near[near['distance_m'] <= 300]['facility_category'].value_counts().to_dict()
        counts_500 = near[near['distance_m'] <= 500]['facility_category'].value_counts().to_dict()
        target_300 = int(near_target[near_target['distance_m'] <= 300].shape[0])
        target_500 = int(near_target[near_target['distance_m'] <= 500].shape[0])
        nearest_target_dist = float(near_target['distance_m'].min()) if len(near_target) else np.nan
        # 공급 공백 점수: 프로그램 관련 기존시설이 가까이 많을수록 낮고, 수요점수가 높을수록 높게 둔다.
        scarcity = 1 / (1 + target_500)
        if not math.isnan(nearest_target_dist):
            scarcity *= min(1.0, nearest_target_dist / 500)
        evidence_demand = float(c['recommended_program_score'])
        supply_gap_adjusted_score = evidence_demand * 0.75 + scarcity * 0.25
        nearest_target_name = near_target.iloc[0]['facility_name'] if len(near_target) else ''
        nearest_target_cat = near_target.iloc[0]['facility_category'] if len(near_target) else ''
        summary_rows.append({
            'candidate_store_id': c['candidate_store_id'],
            'store_name': c['store_name'],
            'brand': c['brand'],
            'admin_dong': c['admin_dong'],
            'road_address': c['road_address'],
            'longitude': c['longitude'],
            'latitude': c['latitude'],
            'recommended_public_facility_program': c['recommended_public_facility_program'],
            'recommended_program_score': c['recommended_program_score'],
            'target_existing_facility_count_300m': target_300,
            'target_existing_facility_count_500m': target_500,
            'nearest_target_existing_facility_name': nearest_target_name,
            'nearest_target_existing_facility_category': nearest_target_cat,
            'nearest_target_existing_facility_distance_m': round(nearest_target_dist, 1) if not math.isnan(nearest_target_dist) else '',
            'all_existing_facility_count_300m': int((near['distance_m'] <= 300).sum()),
            'all_existing_facility_count_500m': int((near['distance_m'] <= 500).sum()),
            'counts_by_category_500m': '; '.join([f'{k}:{v}' for k, v in sorted(counts_500.items())]),
            'supply_gap_adjusted_score': supply_gap_adjusted_score,
            'supply_gap_interpretation': (
                '수요점수는 높지만 프로그램 관련 기존 시설이 500m 내 적어 공급 보완 논리가 강함'
                if target_500 <= 1 else
                '수요는 높으나 주변 관련 시설이 일부 존재하므로 기능 중복을 피한 특화형 운영 필요'
            ),
            'source_note': '시설 공급 검증은 서울시 시설물 정보 2023년 자료 기반이므로 최신 현장 확인 필요'
        })
    detail = pd.DataFrame(detail_rows)
    summary = pd.DataFrame(summary_rows).sort_values('supply_gap_adjusted_score', ascending=False)
    summary['supply_gap_rank'] = range(1, len(summary) + 1)
    summary.to_csv(OUT / 'store_candidate_supply_gap_assessment.csv', index=False, encoding='utf-8-sig')
    detail.to_csv(OUT / 'store_candidate_nearby_existing_facilities_long.csv', index=False, encoding='utf-8-sig')

    with pd.ExcelWriter(OUT / 'store_candidate_supply_gap_assessment.xlsx', engine='openpyxl') as writer:
        summary.to_excel(writer, sheet_name='supply_gap_summary', index=False)
        detail.to_excel(writer, sheet_name='nearby_facilities_long', index=False)
        gangseo[keep_cols].to_excel(writer, sheet_name='gangseo_public_facilities', index=False)

    print('Gangseo facilities:', len(gangseo))
    print('Candidates:', len(candidates))
    print(summary[['supply_gap_rank','store_name','road_address','recommended_public_facility_program','target_existing_facility_count_500m','nearest_target_existing_facility_name','supply_gap_adjusted_score']].head(10).to_string(index=False))

if __name__ == '__main__':
    main()
