import pandas as pd
from pathlib import Path

base = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
inv = pd.read_csv(base/'reanalysis_raw_data_inventory_20260522.csv', encoding='utf-8-sig')
inv['relative_path_l'] = inv['relative_path'].str.lower()

categories = {
    '생활이동/유동인구': ['living_movement', '생활이동', 'movement'],
    '행정코드/경계': ['admin_code', 'jscode', 'boundary', '행정'],
    '상가/상권': ['commercial', 'store_locations', 'store_business', '상가'],
    '편의점 후보/좌표': ['commercial_convenience', 'convenience', 'site_candidates', '편의점', 'candidate'],
    '인구/세대/연령': ['demographics', 'population', 'household', '인구'],
    '교통/지하철': ['transport_timetable', 'subway', '지하철'],
    '병원/의료': ['hospital', 'emergency', 'clinic', '병원'],
    '공항': ['airport', 'kac', '공항'],
    '사업체/마곡': ['business', 'magok', '사업체', '마곡'],
    '주거/1인가구': ['residential', 'one_person'],
    '기존 분석 산출물': ['outputs', 'processed']
}

rows = []
for cat, keys in categories.items():
    mask = inv['relative_path_l'].apply(lambda x: any(k.lower() in x for k in keys))
    subset = inv[mask & ~inv['relative_path'].str.endswith('.gitkeep')]
    rows.append({
        'category': cat,
        'file_count': int(len(subset)),
        'total_mb': round(subset['size_bytes'].sum()/1024/1024, 2),
        'examples': ' | '.join(subset['relative_path'].head(5).tolist())
    })
summary = pd.DataFrame(rows)
summary.to_csv(base/'raw_data_inventory_category_summary.csv', index=False, encoding='utf-8-sig')

requirements = [
    ('2015~2026 상가데이터 추이', '상가/상권', '부분 충족', '현재 상가업소 최신 원자료와 기존 집계 산출물은 있으나 2015~2026 연도별 원자료 전체가 있는지 추가 확인 필요'),
    ('실제 편의점 주소·좌표', '편의점 후보/좌표', '충족 가능', '소상공인 상가업소 자료에서 편의점 업종을 추출해야 함'),
    ('통계청/행정안전부 인구·세대·연령', '인구/세대/연령', '충족', '2019~2026 월말·연말 인구와 연령대 파일 보유'),
    ('주간상주·야간상주·유동인구', '생활이동/유동인구', '부분 충족', '서울 생활이동 2026년 3월 말 4일 보유. 과제 요구상 장기 추이보다 시간대 이용자 구조 분석에 사용 가능'),
    ('24시간·주중주말 시간대', '생활이동/유동인구/교통', '부분 충족', '생활이동 일자와 지하철 시간대 자료 보유. 편의점별 시간대 매출은 없음'),
    ('공항·병원·마곡 배후수요', '공항/병원/사업체', '충족 가능', '공항 통계, 병원 위치, 마곡 입주기업 자료 보유'),
    ('지도·거리뷰 현장 맥락', '지도검색', '추가 확인 필요', '후보 편의점 shortlist 생성 후 네이버/카카오 지도 검색 필요'),
    ('2030 변화 전망', '인구/상권 추이', '부분 충족', '2019~2026 추이 기반 예측은 가능하나 2015~2018 보강 시 더 강함'),
]
req = pd.DataFrame(requirements, columns=['analysis_requirement','linked_data_category','status','notes'])
req.to_csv(base/'raw_data_requirement_gap_table.csv', index=False, encoding='utf-8-sig')

print('SUMMARY')
print(summary.to_string(index=False))
print('\nGAPS')
print(req.to_string(index=False))
