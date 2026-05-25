import pandas as pd
from pathlib import Path

base = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
input_path = base/'inputs'/'small_business_store_info_seoul_202603.csv'
out_dir = base/'outputs'
out_dir.mkdir(parents=True, exist_ok=True)

# 원자료가 매우 클 수 있으므로 필요한 컬럼을 자동 탐색한다.
head = pd.read_csv(input_path, nrows=5, encoding='utf-8-sig')
cols = list(head.columns)
print('COLUMNS')
for c in cols:
    print(c)

# 주요 컬럼 후보명. 소상공인시장진흥공단 상가업소 데이터의 표준 컬럼명을 우선 사용한다.
use_candidates = [
    '상호명','상권업종대분류명','상권업종중분류명','상권업종소분류명',
    '시도명','시군구명','행정동명','법정동명','지번주소','도로명주소',
    '경도','위도','표준산업분류명','상가업소번호'
]
usecols = [c for c in use_candidates if c in cols]
df = pd.read_csv(input_path, usecols=usecols, encoding='utf-8-sig', low_memory=False)

# 강서구 편의점 추출. 데이터분석 과제이므로 상호명 브랜드 검색만으로 확장하지 않고,
# 업종 소분류 또는 표준산업분류가 편의점으로 확인되는 행만 사용한다.
# 상호명에 CU 등이 포함되지만 부동산·학원 등 다른 업종인 행은 오탐이므로 제외한다.
brand_pattern = r'CU|씨유|GS25|GS\s*25|지에스25|세븐일레븐|7-ELEVEN|이마트24|emart24|미니스톱|MINISTOP|편의점'
mask_gangseo = df.get('시군구명', '').astype(str).eq('강서구') if '시군구명' in df.columns else pd.Series(False, index=df.index)
mask_biz_l3 = df.get('상권업종소분류명', '').fillna('').astype(str).str.contains('편의점', case=False, regex=False)
mask_ksic = df.get('표준산업분류명', '').fillna('').astype(str).str.contains('편의점', case=False, regex=False)
mask_conv = mask_biz_l3 | mask_ksic
conv = df[mask_gangseo & mask_conv].copy()

# 브랜드 정규화
def brand_name(name: str) -> str:
    s = str(name).upper().replace(' ', '')
    if 'GS25' in s or '지에스25' in str(name):
        return 'GS25'
    if 'CU' in s or '씨유' in str(name):
        return 'CU'
    if '세븐' in str(name) or '7-ELEVEN' in s:
        return '세븐일레븐'
    if '이마트24' in str(name) or 'EMART24' in s:
        return '이마트24'
    if '미니스톱' in str(name) or 'MINISTOP' in s:
        return '미니스톱'
    return '기타/미분류'

conv['브랜드_정규화'] = conv['상호명'].apply(brand_name) if '상호명' in conv.columns else '미분류'
conv['주소_대표'] = conv['도로명주소'] if '도로명주소' in conv.columns else conv.get('지번주소','')
conv['후보점포ID'] = ['GS_CONV_%04d' % (i+1) for i in range(len(conv))]

# Tableau용 표준 컬럼명
rename_map = {
    '상호명':'store_name', '브랜드_정규화':'brand', '시도명':'sido', '시군구명':'sigungu',
    '행정동명':'admin_dong', '법정동명':'legal_dong', '지번주소':'jibun_address',
    '도로명주소':'road_address', '주소_대표':'address', '경도':'longitude', '위도':'latitude',
    '상권업종대분류명':'biz_l1', '상권업종중분류명':'biz_l2', '상권업종소분류명':'biz_l3',
    '표준산업분류명':'ksic_name', '상가업소번호':'source_store_id', '후보점포ID':'candidate_store_id'
}
conv_out = conv.rename(columns=rename_map)
preferred = ['candidate_store_id','source_store_id','store_name','brand','sido','sigungu','admin_dong','legal_dong','road_address','jibun_address','address','longitude','latitude','biz_l1','biz_l2','biz_l3','ksic_name']
conv_out = conv_out[[c for c in preferred if c in conv_out.columns]]
conv_out.to_csv(out_dir/'tableau_convenience_stores_gangseo.csv', index=False, encoding='utf-8-sig')

# 행정동·브랜드별 요약
summary = conv_out.groupby(['admin_dong','brand'], dropna=False).size().reset_index(name='store_count') if 'admin_dong' in conv_out.columns else pd.DataFrame()
summary.to_csv(out_dir/'convenience_store_count_by_admin_dong_brand.csv', index=False, encoding='utf-8-sig')
admin_summary = conv_out.groupby('admin_dong', dropna=False).agg(
    store_count=('store_name','count'),
    brand_count=('brand','nunique')
).reset_index().sort_values('store_count', ascending=False) if 'admin_dong' in conv_out.columns else pd.DataFrame()
admin_summary.to_csv(out_dir/'convenience_store_count_by_admin_dong.csv', index=False, encoding='utf-8-sig')

# 품질 점검: 좌표 결측, 주소 결측
off_biz = int((~conv_out['biz_l3'].fillna('').astype(str).str.contains('편의점', regex=False)).sum()) if 'biz_l3' in conv_out.columns else None
quality = pd.DataFrame([
    {'check':'total_extracted_gangseo_convenience','value':len(conv_out)},
    {'check':'non_convenience_biz_l3_rows_after_filter','value':off_biz},
    {'check':'missing_longitude','value':int(conv_out['longitude'].isna().sum()) if 'longitude' in conv_out.columns else None},
    {'check':'missing_latitude','value':int(conv_out['latitude'].isna().sum()) if 'latitude' in conv_out.columns else None},
    {'check':'missing_admin_dong','value':int(conv_out['admin_dong'].isna().sum()) if 'admin_dong' in conv_out.columns else None},
    {'check':'unique_admin_dong','value':int(conv_out['admin_dong'].nunique()) if 'admin_dong' in conv_out.columns else None},
])
quality.to_csv(out_dir/'convenience_extraction_quality_checks.csv', index=False, encoding='utf-8-sig')

print('\nEXTRACTION_QUALITY')
print(quality.to_string(index=False))
print('\nTOP_ADMIN_DONGS')
print(admin_summary.head(20).to_string(index=False))
print('\nSAMPLE')
print(conv_out.head(10).to_string(index=False))
