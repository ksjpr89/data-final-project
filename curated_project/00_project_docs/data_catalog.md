# 데이터 카탈로그

이 문서는 현재 프로젝트 폴더에 있는 파일을 **역할, 주제축, 중요도, 추천 위치** 기준으로 정리한 카탈로그입니다. 전체 목록은 `docs/data_catalog.csv`에서 확인할 수 있습니다.

## 파일 역할별 개수

| 역할 | 파일 수 |
|---|---:|
| 분석 산출물 | 45 |
| 스크립트 | 22 |
| 문서 | 17 |
| 정제/분석 데이터 또는 원자료 CSV | 17 |
| 시각화 | 14 |
| 입력 데이터 | 12 |
| 원자료 | 4 |
| 기타 | 2 |
| JSON 원자료/중간 데이터 | 2 |
| 텍스트 추출본/메모 | 2 |
| 엑셀 원자료/분석표 | 1 |
| 압축 패키지 | 1 |

## 주제축별 개수

| 주제축 | 파일 수 |
|---|---:|
| 기타 | 33 |
| 상권·후보지 | 21 |
| 문서 | 15 |
| 1인가구·인구 | 13 |
| 상권·후보지, 시각화 | 8 |
| 공항 | 7 |
| 상권·후보지, 문서 | 6 |
| 시각화 | 4 |
| 공공시설 | 4 |
| 1인가구·인구, 문서 | 4 |
| 공항, 문서 | 3 |
| 1인가구·인구, 시각화 | 3 |
| 기업/R&D | 3 |
| 시각화, 문서 | 2 |
| 상권·후보지, 대시보드 | 2 |
| 병원 | 1 |
| 1인가구·인구, 상권·후보지 | 1 |
| 상권·후보지, 대시보드, 문서 | 1 |
| 공항, 시각화 | 1 |
| 상권·후보지, 공공시설, 문서 | 1 |
| 상권·후보지, 시각화, 문서 | 1 |
| 대시보드 | 1 |
| 공공시설, 대시보드 | 1 |
| 상권·후보지, 공공시설, 대시보드 | 1 |
| 병원, 문서 | 1 |
| 기업/R&D, 문서 | 1 |

## 우선 확인할 핵심 파일

| 파일 | 역할 | 주제축 | 중요도 | 추천 위치 |
|---|---|---|---|---|
| `outputs/expanded_multi_indicator_analysis_20260522/figures/convenience_density_vs_inbound_scatter.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `outputs/expanded_multi_indicator_analysis_20260522/figures/final_ranking_bar_chart.png` | 시각화 | 시각화 | 시각 자료 | `04_outputs/figures/` |
| `outputs/expanded_multi_indicator_analysis_20260522/figures/score_component_heatmap.png` | 시각화 | 시각화 | 시각 자료 | `04_outputs/figures/` |
| `outputs/expanded_multi_indicator_analysis_20260522/figures/store_growth_trend_2019_2025.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `outputs/expanded_multi_indicator_analysis_20260522/figures/top_candidate_radar_chart.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/admin_store_count_and_best_score.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/gangseo_convenience_distribution_top_candidates.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/gimpo_airport_passenger_trend_2016_2025.png` | 시각화 | 공항, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/magok_hypothesis_evidence_strength.png` | 시각화 | 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/magok_population_household_change_comparison.png` | 시각화 | 1인가구·인구, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/magok_young_single_household_specificity_scatter.png` | 시각화 | 1인가구·인구, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/one_person_household_comparison_2024.png` | 시각화 | 1인가구·인구, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/store_context_positioning_scatter.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/figures/top_known_candidate_score_profiles.png` | 시각화 | 상권·후보지, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `reanalysis/outputs/gangseo_one_person_households_findings.md` | 분석 산출물 | 1인가구·인구, 문서 | 핵심 근거 | `04_outputs/tables/ 또는 04_outputs/reports/` |
| `reanalysis/outputs/kac_gimpo_airport_passenger_findings.md` | 분석 산출물 | 공항, 문서 | 핵심 근거 | `04_outputs/tables/ 또는 04_outputs/reports/` |
| `reanalysis/outputs/magok_demographic_specificity_findings.md` | 분석 산출물 | 1인가구·인구, 문서 | 핵심 근거 | `04_outputs/tables/ 또는 04_outputs/reports/` |
| `reanalysis/outputs/magok_specificity_reanalysis_report.md` | 분석 산출물 | 문서 | 최종 제출 핵심 | `04_outputs/tables/ 또는 04_outputs/reports/` |
| `reanalysis/outputs/magok_specificity_synthesis_tables.md` | 분석 산출물 | 문서 | 최종 제출 핵심 | `04_outputs/tables/ 또는 04_outputs/reports/` |
| `reanalysis/raw/gangseo_one_person_households_20250731.xlsx` | 원자료 | 1인가구·인구 | 원자료 | `01_raw_data/` |
| `reanalysis/raw/magok_industrial_complex_infographic_2025.pdf` | 원자료 | 기업/R&D | 원자료 | `01_raw_data/` |
| `reanalysis/raw/magok_industrial_complex_infographic_2025.txt` | 원자료 | 기업/R&D | 원자료 | `01_raw_data/` |
| `reanalysis/source_notes_hospital.md` | 문서 | 병원, 문서 | 핵심 근거 | `00_project_docs/ 또는 04_outputs/reports/` |
| `reanalysis/source_notes_magok_industrial_complex.md` | 문서 | 기업/R&D, 문서 | 핵심 근거 | `00_project_docs/ 또는 04_outputs/reports/` |
| `curated_project/04_outputs/reports/magok_convenience_supply_memo.md` | 분석 산출물 | 상권·후보지, 문서 | 핵심 근거 | `04_outputs/reports/` |
| `curated_project/04_outputs/reports/magok_living_population_analysis_memo.md` | 분석 산출물 | 1인가구·인구, 생활인구·생활이동, 문서 | 핵심 근거 | `04_outputs/reports/` |
| `curated_project/04_outputs/figures/magok_living_population_hourly_weekday_weekend.png` | 시각화 | 1인가구·인구, 생활인구·생활이동, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `curated_project/04_outputs/figures/magok_living_population_age_structure.png` | 시각화 | 1인가구·인구, 생활인구·생활이동, 시각화 | 시각 자료 | `04_outputs/figures/` |
| `curated_project/04_outputs/figures/magok_living_movement_direction_summary.png` | 시각화 | 생활인구·생활이동, 시각화 | 시각 자료 | `04_outputs/figures/` |

## 정리 원칙

파일을 바로 이동하면 기존 스크립트의 상대경로가 깨질 수 있으므로, 먼저 이 카탈로그를 기준으로 핵심 파일과 보관 파일을 구분한 뒤 새 구조에 **복사본을 만드는 방식**이 안전합니다. 새 구조가 안정화되면 스크립트 경로를 고치고, 마지막으로 기존 폴더를 `99_archive/`로 보관하는 순서가 좋습니다.
