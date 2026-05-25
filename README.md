# Data Final Project: 마곡 입지 특수성 및 수요 분석

이 저장소는 마곡 일대의 입지 타당성을 단순 역세권 유동인구가 아니라 **공항 접근성, 대학병원·응급 보호자 수요, 1인가구 구조, 마곡산업단지 R&D 집적**이라는 관점에서 검증한 데이터 분석 프로젝트입니다.

## 지금 가장 먼저 볼 폴더

현재 과제를 다시 차근차근 진행하기 위해 기존 파일을 직접 이동하지 않고, 핵심 파일만 복사한 정리본을 만들었습니다. 다른 PC에서 이어서 작업할 때는 먼저 아래 폴더를 보면 됩니다.

| 경로 | 용도 |
|---|---|
| `curated_project/` | 핵심 원자료, 정제 데이터, 보고서, 차트, 스크립트를 역할별로 다시 모은 정리본 |
| `curated_project/README.md` | 정리본 폴더 사용법과 먼저 볼 파일 안내 |
| `curated_project/00_project_docs/01_magok_specificity_and_data_organization.md` | 마곡 특수성 5개 축과 데이터 정리 방향 |
| `curated_project/00_project_docs/data_catalog.md` | 전체 파일 카탈로그 요약 |
| `curated_project/00_project_docs/curated_file_tree.txt` | 정리본 전체 파일 목록 |

## 프로젝트 목적

초기 분석에서 역 주변 유동인구 중심으로 결론이 흐를 위험이 있었기 때문에, 분석 프레임을 다시 세웠습니다. 본 프로젝트는 마곡이 왜 특수한지, 그리고 그 특수성이 실제 수요 가설로 이어질 수 있는지를 공공데이터와 공식 자료로 검증하는 데 목적이 있습니다.

## 마곡 특수성의 핵심 문장

마곡은 단순히 “역 주변 유동인구가 많은 곳”으로 해석하기보다 **공항 이동 전후 대기 수요, 이대서울병원 응급·보호자 수요, 마곡산단 R&D 근무·방문 수요, 강서구의 큰 1인가구 기반 수요가 겹치는 복합 체류 생활권**으로 해석하는 것이 적절합니다.

## 주요 분석 축

| 분석 축 | 핵심 질문 | 기존 원본 위치 | 정리본 위치 |
|---|---|---|---|
| 공항 수요 | 김포공항 인접성이 실제 이동·대기·체류 수요로 이어질 수 있는가 | `reanalysis/outputs/kac_gimpo_airport_passenger_findings.md` | `curated_project/04_outputs/reports/kac_gimpo_airport_passenger_findings.md` |
| 병원 수요 | 이대서울병원과 응급의료 기능이 보호자·교대근무자 수요를 만들 수 있는가 | `reanalysis/source_notes_hospital.md` | `curated_project/00_project_docs/source_notes_hospital.md` |
| 1인가구 수요 | 강서구와 마곡 후보 생활권은 서울 평균과 다른 1인가구 특성을 보이는가 | `reanalysis/outputs/gangseo_one_person_households_findings.md` | `curated_project/04_outputs/reports/gangseo_one_person_households_findings.md` |
| 기업·R&D 수요 | 마곡산업단지의 기업·연구개발 인력 집적이 장시간 체류 수요를 만들 수 있는가 | `reanalysis/source_notes_magok_industrial_complex.md` | `curated_project/00_project_docs/source_notes_magok_industrial_complex.md` |
| 종합 가설 평가 | 위 수요 축이 후보 입지 판단에 어떤 인사이트를 주는가 | `reanalysis/outputs/magok_specificity_reanalysis_report.md` | `curated_project/04_outputs/reports/magok_specificity_reanalysis_report.md` |
| 편의점 공급 분포 | 마곡 주변에 수요를 받아낼 생활밀착형 공급 거점이 실제로 집중되어 있는가 | `curated_project/02_processed_data/store_and_facility/tableau_convenience_stores_gangseo.csv` | `curated_project/04_outputs/reports/magok_convenience_supply_memo.md` |

## 폴더 구조

| 경로 | 설명 |
|---|---|
| `curated_project/` | 새로 만든 핵심 파일 정리본. 우선 이 폴더부터 보면 됨 |
| `docs/` | 데이터 카탈로그 생성 스크립트와 마곡 특수성 논의 메모 |
| `expanded_inputs/` | 초기 확장 분석에 사용한 외부 입력 데이터 |
| `outputs/` | 초기 후보지·상권·생활이동 분석 결과 |
| `reanalysis/` | 마곡 특수성 재분석 작업 원본 폴더 |
| `reanalysis/inputs/` | 재분석용 입력 원자료 |
| `reanalysis/raw/` | PDF 등 원문 자료와 텍스트 추출본 |
| `reanalysis/outputs/` | 재분석 최종 보고서, 표, 차트, 정제 데이터 |
| `reanalysis/outputs/figures/` | 보고서용 시각화 이미지 |

## 권장 작업 순서

처음부터 최종 결과물을 만들기보다, `curated_project/00_project_docs/01_magok_specificity_and_data_organization.md`를 열고 마곡의 특수성을 먼저 논의하는 방식으로 진행합니다. 이후 공항, 병원, 기업/R&D, 1인가구, 도시 변화 중 하나의 축을 선택해 해당 근거 파일을 읽고, “팩트”, “가설”, “수요로 이어지는 논리”, “추가로 필요한 데이터”를 하나씩 채우는 것이 좋습니다.

## 재현 방법

Python 3.11 환경에서 실행하는 것을 기준으로 했습니다. 사용된 주요 패키지는 `pandas`, `matplotlib`, `openpyxl`, `requests`, `beautifulsoup4`입니다. Manus 샌드박스 기본 환경에서는 이미 설치된 패키지를 중심으로 작업했습니다.

```bash
# 필요 시 패키지 설치
pip install pandas matplotlib openpyxl requests beautifulsoup4

# 주요 재분석 표 생성
python reanalysis/synthesize_magok_specificity_metrics.py

# 보고서용 차트 생성
python reanalysis/create_magok_specificity_charts.py
```

## Git LFS 안내

`reanalysis/inputs/small_business_store_info_seoul_202603.csv` 파일은 100MB를 초과하므로 Git LFS로 추적합니다. 다른 PC에서 전체 원자료까지 받으려면 Git LFS가 설치되어 있어야 합니다.

```bash
git lfs install
git clone https://github.com/ksjpr89/data-final-project.git
cd data-final-project
git lfs pull
```

## 다음 작업 방향

다음 단계에서는 현재 정리된 특수성 축을 후보 건물, 편의점 상부, 공공시설 공급 공백, 시간대별 생활이동 데이터와 연결해야 합니다. 특히 병원 축은 응급실 내원자 수와 보호자 체류시간, 공항 축은 새벽·심야 이동 및 항공 종사자 거주지, 기업 축은 야근·출장·외부 방문객 수요, 1인가구 축은 마곡 법정동 또는 블록 단위 주거유형 자료를 추가로 확보하는 것이 중요합니다. 2026-05-25 기준으로는 강서구 편의점 524개 중 마곡 관련 4개 행정동에 181개가 위치한다는 공급 분석을 추가했으므로, 이후에는 편의점별 300m·500m 반경의 시설·교통·경쟁 밀도를 결합해 실제 후보 지점을 좁히는 것이 적절합니다.
