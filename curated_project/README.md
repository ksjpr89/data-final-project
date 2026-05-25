# Data Final Project — Curated Project Structure

이 폴더는 기존 작업 폴더를 직접 이동하지 않고, 과제 진행에 필요한 핵심 파일만 **읽기 쉬운 구조로 복사**한 정리본입니다. 기존 `reanalysis`, `outputs`, `expanded_inputs` 폴더는 그대로 보존되어 있으므로, 과거 스크립트 경로가 깨지지 않습니다.

## 이 폴더를 만든 이유

현재 프로젝트에는 원자료, 중간 산출물, 스크립트, 시각화, 보고서가 여러 폴더에 섞여 있습니다. 따라서 과제를 다시 이어서 진행할 때 “무엇부터 봐야 하는지”가 불명확합니다. 이 정리본은 마곡 분석을 다시 시작하기 위해 **핵심 파일만 역할별로 모은 내비게이션 폴더**입니다.

## 먼저 볼 문서

| 순서 | 파일 | 내용 |
|---:|---|---|
| 1 | `00_project_docs/01_magok_specificity_and_data_organization.md` | 마곡 특수성 5개 축과 데이터 정리 방향 |
| 2 | `04_outputs/reports/magok_specificity_reanalysis_report.md` | 기존 재분석 보고서 |
| 3 | `04_outputs/tables/magok_specificity_synthesis_tables.md` | 공항·병원·기업·1인가구 핵심 지표표 |
| 4 | `00_project_docs/data_catalog.md` | 전체 파일 카탈로그 요약 |
| 5 | `00_project_docs/curated_file_manifest.csv` | 새 정리 폴더에 복사된 파일 목록 |
| 6 | `00_project_docs/curated_file_tree.txt` | 정리본 폴더의 전체 파일 트리 |

## 마곡 특수성 논의의 출발점

마곡은 단순히 “역 주변 유동인구가 많은 곳”으로 보면 분석이 약해집니다. 이 프로젝트에서는 마곡을 **공항 이동 거점성, 이대서울병원·응급 보호자 수요, 마곡산업단지 R&D 근무·방문 수요, 강서구 1인가구 기반, 10년 사이 도시 변화가 중첩되는 복합 체류 생활권**으로 다룹니다.

| 특수성 축 | 핵심 질문 | 먼저 볼 파일 |
|---|---|---|
| 공항 | 김포공항 인접성이 이동 전후 체류·대기 수요를 만들 수 있는가? | `04_outputs/reports/kac_gimpo_airport_passenger_findings.md` |
| 병원 | 이대서울병원과 응급의료 기능이 보호자·교대근무자 수요를 만들 수 있는가? | `00_project_docs/source_notes_hospital.md` |
| 기업/R&D | 마곡산업단지가 근무자·방문자·협력사 체류 수요를 만들 수 있는가? | `00_project_docs/source_notes_magok_industrial_complex.md` |
| 1인가구·인구 | 강서구와 마곡권의 1인가구 구조가 생활편의 수요와 연결되는가? | `04_outputs/reports/gangseo_one_person_households_findings.md`, `04_outputs/reports/magok_demographic_specificity_findings.md` |
| 도시 변화 | 10년 전과 달라진 마곡의 도시 성격을 데이터로 설명할 수 있는가? | `04_outputs/tables/magok_specificity_synthesis_tables.md` |

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

## 추천 작업 순서

첫 번째 단계에서는 `00_project_docs/01_magok_specificity_and_data_organization.md`를 열고, 마곡을 어떤 특수성으로 설명할지 문장부터 확정하는 것이 좋습니다. 두 번째 단계에서는 공항, 병원, 기업/R&D, 1인가구, 도시 변화 중 하나의 축을 골라 근거 파일을 확인합니다. 세 번째 단계에서는 해당 축에 대해 “팩트”, “가설”, “수요로 이어지는 논리”, “추가로 필요한 데이터”를 정리합니다.

## 주의사항

이 폴더는 **정리용 복사본**입니다. 원본 분석 경로는 기존 폴더에 남아 있으므로, 스크립트를 재실행할 때는 먼저 경로를 확인해야 합니다. 새 구조에서 스크립트를 완전히 재현 가능하게 만들려면 다음 단계에서 상대경로를 새 구조 기준으로 수정해야 합니다.
