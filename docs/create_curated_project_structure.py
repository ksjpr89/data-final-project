from pathlib import Path
import shutil
import csv

ROOT = Path('/home/ubuntu/data_final_analysis_work')
CURATED = ROOT / 'curated_project'

DIRS = [
    '00_project_docs',
    '01_raw_data/airport',
    '01_raw_data/hospital',
    '01_raw_data/one_person_households',
    '01_raw_data/magok_industrial_complex',
    '01_raw_data/business_and_store_context',
    '02_processed_data/airport',
    '02_processed_data/one_person_households',
    '02_processed_data/demographics',
    '02_processed_data/store_and_facility',
    '03_scripts/collection',
    '03_scripts/analysis',
    '03_scripts/visualization',
    '04_outputs/reports',
    '04_outputs/tables',
    '04_outputs/figures',
    '05_tableau_or_dashboard',
    '99_archive/previous_candidate_analysis',
]

COPY_MAP = [
    # Project documents
    ('README.md', '00_project_docs/README_original.md', '프로젝트 최상위 README 원본'),
    ('docs/01_magok_specificity_and_data_organization.md', '00_project_docs/01_magok_specificity_and_data_organization.md', '마곡 특수성 논의 프레임'),
    ('docs/data_catalog.md', '00_project_docs/data_catalog.md', '데이터 카탈로그 요약'),
    ('docs/data_catalog.csv', '00_project_docs/data_catalog.csv', '데이터 카탈로그 전체 CSV'),
    ('reanalysis/README.md', '00_project_docs/reanalysis_README.md', '재분석 폴더 README'),
    ('reanalysis/source_notes_hospital.md', '00_project_docs/source_notes_hospital.md', '이대서울병원 근거 메모'),
    ('reanalysis/source_notes_magok_industrial_complex.md', '00_project_docs/source_notes_magok_industrial_complex.md', '마곡산업단지 근거 메모'),
    ('reanalysis/source_notes_seoul_one_person_age.md', '00_project_docs/source_notes_seoul_one_person_age.md', '서울 1인가구 통계 출처 메모'),
    ('reanalysis/source_notes_seoul_one_person_table_2024.md', '00_project_docs/source_notes_seoul_one_person_table_2024.md', '서울 1인가구 표 메모'),

    # Raw data
    ('reanalysis/raw/gangseo_one_person_households_20250731.xlsx', '01_raw_data/one_person_households/gangseo_one_person_households_20250731.xlsx', '강서구 행정동별 1인가구 원자료'),
    ('reanalysis/raw/magok_industrial_complex_infographic_2025.pdf', '01_raw_data/magok_industrial_complex/magok_industrial_complex_infographic_2025.pdf', '마곡산업단지 2025 실태조사 PDF'),
    ('reanalysis/raw/magok_industrial_complex_infographic_2025.txt', '01_raw_data/magok_industrial_complex/magok_industrial_complex_infographic_2025.txt', '마곡산업단지 PDF 텍스트 추출본'),
    ('reanalysis/web_sources/data_go_kr_15002638.html', '01_raw_data/airport/data_go_kr_15002638.html', '공항 통계 관련 공공데이터포털 HTML 저장본'),
    ('expanded_inputs/gangseo_business_report_2023_based_20250731.xlsx', '01_raw_data/business_and_store_context/gangseo_business_report_2023_based_20250731.xlsx', '강서구 사업체 관련 원자료'),
    ('expanded_inputs/seoul_hospital_clinic_locations_20260508.csv', '01_raw_data/hospital/seoul_hospital_clinic_locations_20260508.csv', '서울 병·의원 위치 원자료'),

    # Processed data and tables
    ('reanalysis/outputs/kac_airport_year_stats_tidy_2016_2025.csv', '02_processed_data/airport/kac_airport_year_stats_tidy_2016_2025.csv', '김포공항 연도별 여객 정제 데이터'),
    ('reanalysis/outputs/kac_airport_year_stats_raw_2016_2025.json', '02_processed_data/airport/kac_airport_year_stats_raw_2016_2025.json', '김포공항 연도별 여객 원 응답 JSON'),
    ('reanalysis/outputs/gangseo_one_person_households_cleaned.csv', '02_processed_data/one_person_households/gangseo_one_person_households_cleaned.csv', '강서구 행정동별 1인가구 정제 데이터'),
    ('reanalysis/outputs/magok_demographic_specificity_summary.csv', '02_processed_data/demographics/magok_demographic_specificity_summary.csv', '마곡권 인구·가구 비교 요약'),
    ('reanalysis/outputs/tableau_convenience_stores_gangseo.csv', '02_processed_data/store_and_facility/tableau_convenience_stores_gangseo.csv', '강서구 편의점 대시보드용 데이터'),
    ('reanalysis/outputs/tableau_existing_public_facilities_gangseo.csv', '02_processed_data/store_and_facility/tableau_existing_public_facilities_gangseo.csv', '강서구 기존 공공시설 대시보드용 데이터'),
    ('reanalysis/outputs/tableau_store_level_context_metrics.csv', '02_processed_data/store_and_facility/tableau_store_level_context_metrics.csv', '점포 단위 맥락 지표'),
    ('reanalysis/outputs/tableau_store_public_facility_program_scores.csv', '02_processed_data/store_and_facility/tableau_store_public_facility_program_scores.csv', '점포별 공공시설 프로그램 점수'),
    ('reanalysis/outputs/store_candidate_supply_gap_assessment.xlsx', '02_processed_data/store_and_facility/store_candidate_supply_gap_assessment.xlsx', '후보지 공급 공백 평가 엑셀'),

    # Reports and findings
    ('reanalysis/outputs/magok_specificity_reanalysis_report.md', '04_outputs/reports/magok_specificity_reanalysis_report.md', '마곡 특수성 재분석 최종 보고서'),
    ('reanalysis/outputs/magok_specificity_synthesis_tables.md', '04_outputs/tables/magok_specificity_synthesis_tables.md', '마곡 특수성 종합 지표 테이블'),
    ('reanalysis/outputs/kac_gimpo_airport_passenger_findings.md', '04_outputs/reports/kac_gimpo_airport_passenger_findings.md', '김포공항 여객 분석 요약'),
    ('reanalysis/outputs/gangseo_one_person_households_findings.md', '04_outputs/reports/gangseo_one_person_households_findings.md', '강서구 1인가구 분석 요약'),
    ('reanalysis/outputs/magok_demographic_specificity_findings.md', '04_outputs/reports/magok_demographic_specificity_findings.md', '마곡권 인구 특수성 분석 요약'),
    ('reanalysis/outputs/figure_review_notes.md', '04_outputs/reports/figure_review_notes.md', '차트 검수 메모'),

    # Scripts
    ('reanalysis/collect_kac_airport_year_stats.py', '03_scripts/collection/collect_kac_airport_year_stats.py', '한국공항공사 통계 수집 스크립트'),
    ('reanalysis/inspect_gangseo_one_person.py', '03_scripts/analysis/inspect_gangseo_one_person.py', '강서구 1인가구 엑셀 구조 확인 스크립트'),
    ('reanalysis/analyze_gangseo_one_person.py', '03_scripts/analysis/analyze_gangseo_one_person.py', '강서구 1인가구 분석 스크립트'),
    ('reanalysis/synthesize_magok_specificity_metrics.py', '03_scripts/analysis/synthesize_magok_specificity_metrics.py', '마곡 특수성 지표 종합 스크립트'),
    ('reanalysis/create_magok_specificity_charts.py', '03_scripts/visualization/create_magok_specificity_charts.py', '마곡 특수성 차트 생성 스크립트'),
    ('docs/build_data_catalog.py', '03_scripts/analysis/build_data_catalog.py', '데이터 카탈로그 생성 스크립트'),

    # Tableau/dashboard
    ('reanalysis/outputs/tableau_dashboard_guide.md', '05_tableau_or_dashboard/tableau_dashboard_guide.md', 'Tableau 대시보드 가이드'),
    ('reanalysis/outputs/tableau_data_dictionary.md', '05_tableau_or_dashboard/tableau_data_dictionary.md', 'Tableau 데이터 딕셔너리'),
]

FIGURE_SRC_DIR = ROOT / 'reanalysis' / 'outputs' / 'figures'
PREVIOUS_FIGURE_SRC_DIR = ROOT / 'outputs' / 'expanded_multi_indicator_analysis_20260522' / 'figures'


def copy_file(src_rel: str, dst_rel: str) -> tuple[str, str, str]:
    src = ROOT / src_rel
    dst = CURATED / dst_rel
    if not src.exists():
        return (src_rel, dst_rel, 'missing')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return (src_rel, dst_rel, 'copied')


def main():
    for d in DIRS:
        (CURATED / d).mkdir(parents=True, exist_ok=True)

    log_rows = []
    for src, dst, desc in COPY_MAP:
        src_rel, dst_rel, status = copy_file(src, dst)
        log_rows.append({'source': src_rel, 'curated_path': dst_rel, 'description': desc, 'status': status})

    if FIGURE_SRC_DIR.exists():
        for fig in sorted(FIGURE_SRC_DIR.glob('*.png')):
            dst = f'04_outputs/figures/{fig.name}'
            src_rel, dst_rel, status = copy_file(str(fig.relative_to(ROOT)), dst)
            log_rows.append({'source': src_rel, 'curated_path': dst_rel, 'description': '마곡 재분석 시각화', 'status': status})

    if PREVIOUS_FIGURE_SRC_DIR.exists():
        for fig in sorted(PREVIOUS_FIGURE_SRC_DIR.glob('*.png')):
            dst = f'99_archive/previous_candidate_analysis/figures/{fig.name}'
            src_rel, dst_rel, status = copy_file(str(fig.relative_to(ROOT)), dst)
            log_rows.append({'source': src_rel, 'curated_path': dst_rel, 'description': '이전 후보지 분석 시각화 보관', 'status': status})

    with (CURATED / '00_project_docs' / 'curated_file_manifest.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['source', 'curated_path', 'description', 'status'])
        writer.writeheader()
        writer.writerows(log_rows)

    readme = '''# Curated Project Structure

이 폴더는 기존 작업 폴더를 직접 이동하지 않고, 과제 진행에 필요한 핵심 파일만 **읽기 쉬운 구조로 복사**한 정리본입니다. 기존 `reanalysis`, `outputs`, `expanded_inputs` 폴더는 그대로 보존되어 있으므로, 과거 스크립트 경로가 깨지지 않습니다.

## 먼저 볼 문서

| 순서 | 파일 | 내용 |
|---:|---|---|
| 1 | `00_project_docs/01_magok_specificity_and_data_organization.md` | 마곡 특수성 5개 축과 데이터 정리 방향 |
| 2 | `04_outputs/reports/magok_specificity_reanalysis_report.md` | 기존 재분석 보고서 |
| 3 | `04_outputs/tables/magok_specificity_synthesis_tables.md` | 공항·병원·기업·1인가구 핵심 지표표 |
| 4 | `00_project_docs/data_catalog.md` | 전체 파일 카탈로그 요약 |
| 5 | `00_project_docs/curated_file_manifest.csv` | 새 정리 폴더에 복사된 파일 목록 |

## 폴더 설명

| 폴더 | 설명 |
|---|---|
| `00_project_docs/` | 과제 기획, 마곡 특수성 논의, 출처 메모, 데이터 카탈로그 |
| `01_raw_data/` | 원자료와 공식 출처 파일 |
| `02_processed_data/` | 분석에 바로 사용할 수 있는 정제 데이터 |
| `03_scripts/` | 수집·정제·분석·시각화 스크립트 복사본 |
| `04_outputs/` | 보고서, 표, 차트 등 최종 산출물 |
| `05_tableau_or_dashboard/` | Tableau 또는 대시보드용 자료 |
| `99_archive/` | 이전 방향의 후보지 분석 자료 보관 |

## 주의사항

이 폴더는 **정리용 복사본**입니다. 원본 분석 경로는 기존 폴더에 남아 있으므로, 스크립트를 재실행할 때는 먼저 경로를 확인해야 합니다. 새 구조에서 스크립트를 완전히 재현 가능하게 만들려면 다음 단계에서 상대경로를 새 구조 기준으로 수정해야 합니다.
'''
    (CURATED / 'README.md').write_text(readme, encoding='utf-8')

    missing = [r for r in log_rows if r['status'] == 'missing']
    print(f'curated_dir={CURATED}')
    print(f'copied={sum(r["status"] == "copied" for r in log_rows)}')
    print(f'missing={len(missing)}')
    if missing:
        print('missing files:')
        for r in missing:
            print('-', r['source'])

if __name__ == '__main__':
    main()
