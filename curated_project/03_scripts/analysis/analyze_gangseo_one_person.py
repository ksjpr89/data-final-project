from pathlib import Path
import pandas as pd

raw = Path('/home/ubuntu/data_final_analysis_work/reanalysis/raw/gangseo_one_person_households_20250731.xlsx')
outdir = Path('/home/ubuntu/data_final_analysis_work/reanalysis/outputs')
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(raw, sheet_name=0, header=None, skiprows=2, names=['dong','one_person_households'])
df['dong'] = df['dong'].astype(str).str.replace('\u3000','', regex=False).str.strip()
df['one_person_households'] = pd.to_numeric(df['one_person_households'], errors='coerce')
df = df.dropna(subset=['one_person_households']).copy()
df['one_person_households'] = df['one_person_households'].astype(int)
total = int(df.loc[df['dong'].eq('강서구'), 'one_person_households'].iloc[0])
dong = df[~df['dong'].eq('강서구')].copy()
dong['share_of_gangseo_pct'] = dong['one_person_households'] / total * 100
# 강서구에는 2024년 통계상 행정동 '마곡동'이 별도 존재하지 않는다.
# 법정동 마곡동은 생활권·주소상 가양1동, 발산1동, 공항동, 방화1동 일부와 연동해 해석해야 한다.
# 따라서 아래 후보군은 '마곡 법정동 및 마곡산업단지·이대서울병원·공항 접근권'을 포괄하는 분석용 근사치이다.
magok_related = ['가양1동','발산1동','공항동','방화1동']
dong['magok_related_flag'] = dong['dong'].isin(magok_related)

summary = {
    'gangseo_total_one_person_households_2024': total,
    'top_dong': dong.sort_values('one_person_households', ascending=False).iloc[0]['dong'],
    'top_dong_households': int(dong.sort_values('one_person_households', ascending=False).iloc[0]['one_person_households']),
    'administrative_magok_dong_exists': False,
    'note': '2024년 강서구 행정동별 KOSIS 집계에는 행정동 마곡동이 별도 항목으로 존재하지 않아 가양1동·발산1동·공항동·방화1동을 마곡 관련 후보권역으로 묶어 해석한다.',
    'magok_related_households': int(dong.loc[dong['magok_related_flag'], 'one_person_households'].sum()),
    'magok_related_share_of_gangseo_pct': float(dong.loc[dong['magok_related_flag'], 'one_person_households'].sum() / total * 100),
}

csv_path = outdir / 'gangseo_one_person_households_by_dong_2024.csv'
dong.to_csv(csv_path, index=False, encoding='utf-8-sig')

md = []
md.append('# 강서구 행정동별 1인가구 현황 2024 정제 결과\n')
md.append('자료원: 서울 열린데이터광장 「서울특별시 강서구_행정동별 1인가구 현황」 최신 파일(수정일 2025-08-19), 원천 통계는 KOSIS 「가구원수별 가구 - 읍면동」, 2024년 일반가구 기준입니다.\n')
md.append('## 핵심 수치\n')
for k,v in summary.items():
    md.append(f'- {k}: {v}\n')
md.append('\n## 행정동별 1인가구 상위 10개 동\n\n')
md.append(dong.sort_values('one_person_households', ascending=False).head(10)[['dong','one_person_households','share_of_gangseo_pct','magok_related_flag']].to_markdown(index=False, floatfmt='.2f'))
md.append('\n\n## 마곡 관련 후보 행정동\n\n')
md.append(dong[dong['magok_related_flag']][['dong','one_person_households','share_of_gangseo_pct']].sort_values('one_person_households', ascending=False).to_markdown(index=False, floatfmt='.2f'))
md.append('\n')
(outdir / 'gangseo_one_person_households_findings.md').write_text('\n'.join(md), encoding='utf-8')
print('saved', csv_path)
print(pd.Series(summary).to_string())
print('\nTOP 10')
print(dong.sort_values('one_person_households', ascending=False).head(10).to_string(index=False))
