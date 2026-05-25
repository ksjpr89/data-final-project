from pathlib import Path
import pandas as pd

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)

# 1. Airport summary
airport = pd.read_csv(OUT / 'kac_gimpo_airport_passenger_summary_2016_2025.csv')
a2019 = airport.loc[airport['year'] == 2019].iloc[0]
a2025 = airport.loc[airport['year'] == 2025].iloc[0]

airport_metrics = pd.DataFrame([
    {'metric': '김포공항 총여객', 'baseline': '2019', 'baseline_value': a2019['gimpo_passenger_total'], 'latest': '2025', 'latest_value': a2025['gimpo_passenger_total'], 'change_pct': (a2025['gimpo_passenger_total']/a2019['gimpo_passenger_total']-1)*100, 'interpretation': '코로나 이후에도 연 2,296만 명 수준의 대형 공항 수요가 유지된다.'},
    {'metric': '김포공항 국내선 비중', 'baseline': '2019', 'baseline_value': a2019['gimpo_domestic_ratio_pct'], 'latest': '2025', 'latest_value': a2025['gimpo_domestic_ratio_pct'], 'change_pct': a2025['gimpo_domestic_ratio_pct']-a2019['gimpo_domestic_ratio_pct'], 'interpretation': '여전히 국내선 중심이지만 국제선 비중이 2025년 19.33%까지 회복했다.'},
    {'metric': '김포공항 KAC 공항 내 여객 점유율', 'baseline': '2019', 'baseline_value': a2019['gimpo_share_of_kac_airports_total_pct'], 'latest': '2025', 'latest_value': a2025['gimpo_share_of_kac_airports_total_pct'], 'change_pct': a2025['gimpo_share_of_kac_airports_total_pct']-a2019['gimpo_share_of_kac_airports_total_pct'], 'interpretation': '전국 공항 포트폴리오 내 점유율은 낮아졌지만 마곡 인근 공항 거점성은 절대 규모로 유효하다.'},
])

# 2. Seoul/Gangseo one-person household comparison
seoul_total_one_person = 1660813
seoul_gu_avg = seoul_total_one_person / 25
gangseo_one_person = 106748
magok_related_one_person = 24924
one_person_metrics = pd.DataFrame([
    {'metric': '서울 전체 1인가구', 'value': seoul_total_one_person, 'comparison': '2024년 자치구 전체 합계'},
    {'metric': '서울 자치구 평균 1인가구', 'value': round(seoul_gu_avg), 'comparison': '서울 전체/25개 자치구 단순 평균'},
    {'metric': '강서구 1인가구', 'value': gangseo_one_person, 'comparison': f'서울 자치구 평균 대비 {gangseo_one_person/seoul_gu_avg:.2f}배'},
    {'metric': '마곡 관련 후보 행정동 1인가구', 'value': magok_related_one_person, 'comparison': f'강서구 전체의 {magok_related_one_person/gangseo_one_person*100:.2f}%'},
])

# 3. Demographic comparison
comp = pd.read_csv(OUT / 'magok_demographic_specificity_comparison.csv')
# Preserve only columns useful in final narrative
keep_cols = [c for c in ['comparison_unit','population_2019','population_latest','population_change_pct','households_2019','households_latest','household_change_pct','avg_household_size_latest','age_20_39_share_latest','age_60plus_share_latest','one_person_household_share_latest'] if c in comp.columns]
demo = comp[keep_cols].copy()

# 4. Enterprise metrics from source note as structured table
enterprise_metrics = pd.DataFrame([
    {'metric': '2025년 마곡사업장 전체 근무인원', 'value': 39966, 'unit': '명', 'comparison': '전년 대비 11.1% 증가'},
    {'metric': '2025년 마곡사업장 연구개발 인력', 'value': 18301, 'unit': '명', 'comparison': '전체 근무인원의 45.8%'},
    {'metric': '2024년 마곡사업장 매출액', 'value': 23.7, 'unit': '조 원', 'comparison': '전년 대비 4.0% 증가'},
    {'metric': '2024년 연구개발 투자액', 'value': 12.2, 'unit': '조 원', 'comparison': '전년 대비 4.5% 증가'},
])

# 5. Hypothesis evidence matrix
hypothesis = pd.DataFrame([
    {'hypothesis': '공항 인근 1인·단기 체류 수요', 'evidence_level': '중상', 'key_metric': '김포공항 2025년 총여객 2,296만 명, 국내선 80.67%', 'caveat': '항공 종사자 거주지·승무원 숙박 수요는 직접 자료가 추가 필요'},
    {'hypothesis': '대학병원 교대근무·응급 보호자 수요', 'evidence_level': '중상', 'key_metric': '이대서울병원 1,014병상, 2024년 거점 지역응급의료센터 지정', 'caveat': '병원 직원 수와 응급실 방문자 수의 공개 원자료가 추가 필요'},
    {'hypothesis': '마곡산단 기업 유입에 따른 근무·방문 수요', 'evidence_level': '상', 'key_metric': '2025년 마곡사업장 근무인원 39,966명, R&D 인력 18,301명', 'caveat': '야간 체류·출장·프로젝트 단기 숙박 비중은 별도 조사가 필요'},
    {'hypothesis': '서울 평균과 다른 1인가구 집적', 'evidence_level': '상', 'key_metric': '강서구 1인가구 106,748가구, 서울 자치구 평균의 1.61배', 'caveat': '마곡 법정동이 별도 행정동으로 집계되지 않아 생활권 근사 필요'},
    {'hypothesis': '마곡핵심권의 청년·소가구 특수성', 'evidence_level': '중', 'key_metric': '마곡핵심권 20~39세 비중 35.53%, 강서구 전체 30.39%', 'caveat': '발산1동은 가양1동보다 1인가구 신호가 약해 내부 세분화 필요'},
])

files = {
    'magok_specificity_airport_metrics.csv': airport_metrics,
    'magok_specificity_one_person_metrics.csv': one_person_metrics,
    'magok_specificity_demographic_comparison_selected.csv': demo,
    'magok_specificity_enterprise_metrics.csv': enterprise_metrics,
    'magok_specificity_hypothesis_evidence_matrix.csv': hypothesis,
}
for name, df in files.items():
    df.to_csv(OUT / name, index=False, encoding='utf-8-sig')

# Write markdown tables for easy insertion
md = []
md.append('# 마곡 특수성 종합 지표 테이블\n')
for title, df in [
    ('공항 수요 지표', airport_metrics),
    ('1인가구 비교 지표', one_person_metrics),
    ('마곡·공항·강서 인구구조 비교', demo),
    ('마곡산업단지 기업 변화 지표', enterprise_metrics),
    ('가설별 근거 강도 평가', hypothesis),
]:
    md.append(f'## {title}\n')
    md.append(df.to_markdown(index=False))
    md.append('\n')
(OUT / 'magok_specificity_synthesis_tables.md').write_text('\n'.join(md), encoding='utf-8')
print('saved synthesis tables')
for name in files:
    print(OUT / name)
print(OUT / 'magok_specificity_synthesis_tables.md')
