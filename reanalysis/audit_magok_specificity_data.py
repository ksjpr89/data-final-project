from pathlib import Path
import pandas as pd
import json

BASE = Path('/home/ubuntu/data_final_analysis_work')
OUT = BASE / 'reanalysis' / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)

files = [
    BASE/'outputs/candidate_demographics_by_period.csv',
    BASE/'reanalysis/inputs/gangseo_demographics_by_dong_period.csv',
    BASE/'outputs/candidate_living_movement_avg_daily_direction.csv',
    BASE/'expanded_inputs/candidate_living_movement_avg_daily_direction.csv',
    BASE/'expanded_inputs/kac_airport_transport_statistics_20250915.csv',
    BASE/'expanded_inputs/magok_tenant_companies_20260213.xlsx',
    BASE/'expanded_inputs/gangseo_business_report_2023_based_20250731.xlsx',
    BASE/'expanded_inputs/seoul_hospital_clinic_locations_20260508.csv',
    BASE/'expanded_inputs/seoul_subway_station_hourly_20260506.csv',
    BASE/'reanalysis/outputs/tableau_convenience_stores_gangseo.csv',
    BASE/'reanalysis/outputs/tableau_existing_public_facilities_gangseo.csv',
    BASE/'reanalysis/outputs/tableau_store_level_context_metrics.csv',
]

rows = []
for p in files:
    if not p.exists():
        rows.append({'file': str(p.relative_to(BASE)), 'exists': False, 'rows': None, 'cols': None, 'columns': '', 'sample_values': '', 'read_note': 'missing'})
        continue
    try:
        if p.suffix.lower() in ['.xlsx', '.xls']:
            xls = pd.ExcelFile(p)
            for sheet in xls.sheet_names[:5]:
                try:
                    df = pd.read_excel(p, sheet_name=sheet, nrows=5)
                    rows.append({
                        'file': str(p.relative_to(BASE)) + f'::{sheet}',
                        'exists': True,
                        'rows': 'sheet_unknown',
                        'cols': len(df.columns),
                        'columns': ' | '.join(map(str, df.columns.tolist()[:80])),
                        'sample_values': json.dumps(df.head(2).astype(str).to_dict(orient='records'), ensure_ascii=False)[:1500],
                        'read_note': 'excel_preview'
                    })
                except Exception as e:
                    rows.append({'file': str(p.relative_to(BASE))+f'::{sheet}', 'exists': True, 'rows': None, 'cols': None, 'columns': '', 'sample_values': '', 'read_note': f'sheet_error: {e}'})
        else:
            # try encodings
            last = None
            for enc in ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']:
                try:
                    df = pd.read_csv(p, encoding=enc, nrows=10)
                    full_rows = sum(1 for _ in open(p, 'rb')) - 1
                    rows.append({
                        'file': str(p.relative_to(BASE)),
                        'exists': True,
                        'rows': full_rows,
                        'cols': len(df.columns),
                        'columns': ' | '.join(map(str, df.columns.tolist()[:120])),
                        'sample_values': json.dumps(df.head(3).astype(str).to_dict(orient='records'), ensure_ascii=False)[:1800],
                        'read_note': f'csv_preview:{enc}'
                    })
                    break
                except Exception as e:
                    last = e
            else:
                rows.append({'file': str(p.relative_to(BASE)), 'exists': True, 'rows': None, 'cols': None, 'columns': '', 'sample_values': '', 'read_note': f'csv_error: {last}'})
    except Exception as e:
        rows.append({'file': str(p.relative_to(BASE)), 'exists': True, 'rows': None, 'cols': None, 'columns': '', 'sample_values': '', 'read_note': f'error: {e}'})

audit = pd.DataFrame(rows)
audit.to_csv(OUT/'magok_specificity_data_audit.csv', index=False, encoding='utf-8-sig')

# 가설별 데이터 상태표
hypotheses = [
    {
        'hypothesis': '마곡은 서울 평균 대비 최근 10년간 인구·가구 구조가 빠르게 변했다',
        'available_data': 'gangseo_demographics_by_dong_period.csv; candidate_demographics_by_period.csv',
        'available_level': '강서구 행정동 패널은 있음. 서울 전체 평균 비교 원자료는 현재 샌드박스 목록에서 미확인.',
        'gap': '서울 전체 행정동 또는 자치구 평균의 동일 기간 1인가구·연령구조 자료 필요',
        'priority': 'high'
    },
    {
        'hypothesis': '마곡은 공항 접근 거점이며 공항 관련 이동·근무 수요가 있다',
        'available_data': 'kac_airport_transport_statistics_20250915.csv; subway station/hourly data; 생활이동 자료',
        'available_level': '공항 통계와 역 승하차, 강서 후보동 생활이동은 있음.',
        'gap': '공항 종사자 거주지 또는 공항 관련 업종 종사자 위치 자료는 미확인. 대체지표로 공항 접근성·공항 통계·생활이동 사용 필요',
        'priority': 'high'
    },
    {
        'hypothesis': '대학병원 때문에 병원 관계자 교대근무 및 응급 보호자 휴게 수요가 있다',
        'available_data': 'seoul_hospital_clinic_locations_20260508.csv; hospital radius metrics in store context',
        'available_level': '병원·의원 위치 및 후보 편의점 반경 의료시설 수는 있음.',
        'gap': '병원 종사자 수, 응급실 방문자 수, 보호자 대기 수요 직접 자료는 미확인. 병원 규모·응급의료기관 자료 추가 필요',
        'priority': 'high'
    },
    {
        'hypothesis': '기업 유입으로 마곡은 10년 전과 다른 업무·연구개발 지구가 되었다',
        'available_data': 'magok_tenant_companies_20260213.xlsx; gangseo_business_report_2023_based_20250731.xlsx; store industry by year',
        'available_level': '입주기업 목록과 사업체 통계, 상권 변화 자료가 있음.',
        'gap': '서울 평균 대비 사업체·종사자 증가율 비교표 필요. 10년 전 기준 연도 정합성 확인 필요',
        'priority': 'high'
    },
    {
        'hypothesis': '기존 공공시설 공급 공백이 있어 편의점 위 공공시설이 필요하다',
        'available_data': 'tableau_existing_public_facilities_gangseo.csv; store_candidate_supply_gap_assessment.csv',
        'available_level': '강서구 시설물 위치와 후보 반경 공급 지표는 있음.',
        'gap': '시설 유형 분류가 실제 청년·휴게·보호자 쉼터 수요와 맞는지 수동 검증 필요',
        'priority': 'medium'
    },
]
pd.DataFrame(hypotheses).to_csv(OUT/'magok_specificity_hypothesis_data_gap_matrix.csv', index=False, encoding='utf-8-sig')

print('saved', OUT/'magok_specificity_data_audit.csv')
print('saved', OUT/'magok_specificity_hypothesis_data_gap_matrix.csv')
print(audit[['file','exists','rows','cols','read_note']].to_string(index=False))
