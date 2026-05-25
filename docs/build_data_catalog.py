from pathlib import Path
import csv

ROOT = Path('/home/ubuntu/data_final_analysis_work')
OUT_CSV = ROOT / 'docs' / 'data_catalog.csv'
OUT_MD = ROOT / 'docs' / 'data_catalog.md'

IGNORE_PARTS = {'.git', '__pycache__'}

TYPE_BY_EXT = {
    '.csv': '정제/분석 데이터 또는 원자료 CSV',
    '.json': 'JSON 원자료/중간 데이터',
    '.xlsx': '엑셀 원자료/분석표',
    '.xls': '엑셀 원자료/분석표',
    '.pdf': 'PDF 원문 자료',
    '.txt': '텍스트 추출본/메모',
    '.md': '문서/보고서/조사 메모',
    '.py': '수집·정제·분석 스크립트',
    '.png': '시각화 이미지',
    '.html': '웹 원문 저장본',
    '.zip': '압축 패키지',
}

KEYWORDS = [
    ('airport|kac|gimpo|공항|김포', '공항'),
    ('hospital|eumc|병원|응급|이대서울', '병원'),
    ('one_person|1인가구|household|demographic|population|인구|가구', '1인가구·인구'),
    ('magok_industrial|enterprise|industrial|산업단지|기업|R&D|rnd', '기업/R&D'),
    ('store|convenience|candidate|상권|편의점|후보', '상권·후보지'),
    ('facility|public|공공시설', '공공시설'),
    ('tableau|dashboard', '대시보드'),
    ('figure|figures|chart|scatter|trend|visual', '시각화'),
    ('report|findings|summary|synthesis|README|notes|메모|보고서', '문서'),
]

IMPORTANCE_RULES = [
    ('magok_specificity_reanalysis_report.md', '최종 제출 핵심'),
    ('magok_specificity_synthesis_tables.md', '최종 제출 핵심'),
    ('kac_gimpo_airport_passenger_findings.md', '핵심 근거'),
    ('gangseo_one_person_households_findings.md', '핵심 근거'),
    ('magok_demographic_specificity_findings.md', '핵심 근거'),
    ('source_notes_hospital.md', '핵심 근거'),
    ('source_notes_magok_industrial_complex.md', '핵심 근거'),
    ('figures/', '시각 자료'),
    ('.py', '재현용 스크립트'),
    ('raw/', '원자료'),
    ('inputs/', '입력 데이터'),
]


def infer_topic(path: str) -> str:
    lower = path.lower()
    topics = []
    for pattern, topic in KEYWORDS:
        for token in pattern.split('|'):
            if token.lower() in lower:
                topics.append(topic)
                break
    if not topics:
        return '기타'
    # preserve order, unique
    seen = []
    for t in topics:
        if t not in seen:
            seen.append(t)
    return ', '.join(seen)


def infer_role(p: Path) -> str:
    s = str(p).replace('\\', '/')
    ext = p.suffix.lower()
    if '/raw/' in s or '/web_sources/' in s:
        return '원자료'
    if '/inputs/' in s or 'expanded_inputs/' in s:
        return '입력 데이터'
    if '/outputs/figures/' in s or ext == '.png':
        return '시각화'
    if '/outputs/' in s and ext in {'.md', '.csv', '.xlsx', '.json'}:
        return '분석 산출물'
    if ext == '.py':
        return '스크립트'
    if ext == '.md':
        return '문서'
    return TYPE_BY_EXT.get(ext, '기타')


def infer_importance(path: str) -> str:
    for token, label in IMPORTANCE_RULES:
        if token in path:
            return label
    if path.startswith('outputs/expanded_multi_indicator_analysis_20260522'):
        return '이전 분석 보관'
    return '참고/보관'


def infer_recommended_location(path: str, role: str, topic: str) -> str:
    if role == '원자료':
        return '01_raw_data/'
    if role == '입력 데이터':
        return '01_raw_data/ 또는 02_processed_data/ 검토 필요'
    if role == '스크립트':
        return '03_scripts/'
    if role == '시각화':
        return '04_outputs/figures/'
    if role == '분석 산출물':
        return '04_outputs/tables/ 또는 04_outputs/reports/'
    if role == '문서':
        return '00_project_docs/ 또는 04_outputs/reports/'
    if '대시보드' in topic:
        return '05_tableau_or_dashboard/'
    return '99_archive/ 또는 검토 필요'

rows = []
for p in sorted(ROOT.rglob('*')):
    rel = p.relative_to(ROOT)
    if any(part in IGNORE_PARTS for part in rel.parts):
        continue
    if not p.is_file():
        continue
    rel_s = str(rel).replace('\\', '/')
    role = infer_role(rel)
    topic = infer_topic(rel_s)
    rows.append({
        'path': rel_s,
        'file_name': p.name,
        'extension': p.suffix.lower() or '(none)',
        'size_mb': f'{p.stat().st_size/1024/1024:.3f}',
        'role': role,
        'topic': topic,
        'importance': infer_importance(rel_s),
        'recommended_location': infer_recommended_location(rel_s, role, topic),
        'note': '',
    })

with OUT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

# Markdown summary: 핵심 파일 위주 + 전체 분류 요약
from collections import Counter
role_counts = Counter(r['role'] for r in rows)
topic_counts = Counter(r['topic'] for r in rows)
important = [r for r in rows if r['importance'] in {'최종 제출 핵심', '핵심 근거', '시각 자료', '원자료'}]

lines = []
lines.append('# 데이터 카탈로그')
lines.append('')
lines.append('이 문서는 현재 프로젝트 폴더에 있는 파일을 **역할, 주제축, 중요도, 추천 위치** 기준으로 정리한 카탈로그입니다. 전체 목록은 `docs/data_catalog.csv`에서 확인할 수 있습니다.')
lines.append('')
lines.append('## 파일 역할별 개수')
lines.append('')
lines.append('| 역할 | 파일 수 |')
lines.append('|---|---:|')
for k, v in role_counts.most_common():
    lines.append(f'| {k} | {v} |')
lines.append('')
lines.append('## 주제축별 개수')
lines.append('')
lines.append('| 주제축 | 파일 수 |')
lines.append('|---|---:|')
for k, v in topic_counts.most_common():
    lines.append(f'| {k} | {v} |')
lines.append('')
lines.append('## 우선 확인할 핵심 파일')
lines.append('')
lines.append('| 파일 | 역할 | 주제축 | 중요도 | 추천 위치 |')
lines.append('|---|---|---|---|---|')
for r in important[:80]:
    lines.append(f"| `{r['path']}` | {r['role']} | {r['topic']} | {r['importance']} | `{r['recommended_location']}` |")
lines.append('')
lines.append('## 정리 원칙')
lines.append('')
lines.append('파일을 바로 이동하면 기존 스크립트의 상대경로가 깨질 수 있으므로, 먼저 이 카탈로그를 기준으로 핵심 파일과 보관 파일을 구분한 뒤 새 구조에 **복사본을 만드는 방식**이 안전합니다. 새 구조가 안정화되면 스크립트 경로를 고치고, 마지막으로 기존 폴더를 `99_archive/`로 보관하는 순서가 좋습니다.')
OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')

print(f'created {OUT_CSV}')
print(f'created {OUT_MD}')
print(f'rows={len(rows)}')
