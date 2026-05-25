from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
FIG = OUT / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

# Korean font
font_candidates = ['Noto Sans CJK KR', 'Noto Sans CJK JP', 'NanumGothic', 'DejaVu Sans']
available = {f.name for f in fm.fontManager.ttflist}
for f in font_candidates:
    if f in available:
        plt.rcParams['font.family'] = f
        break
plt.rcParams['axes.unicode_minus'] = False

DEMOG = BASE / 'inputs' / 'gangseo_demographics_by_dong_period.csv'
df = pd.read_csv(DEMOG, encoding='utf-8-sig')
for col in ['resident_population','households','pop_20_39','pop_60_plus','avg_household_size','share_20_39_pct','share_60_plus_pct']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

def pct_change(new, old):
    if pd.isna(new) or pd.isna(old) or old == 0:
        return np.nan
    return (new / old - 1) * 100

# 분석 범위: 마곡 행정동은 별도 행정동이 없으므로 마곡 생활권을 발산1동·가양1동으로 정의한다.
# 공항 접근성과 연계되는 보조 생활권은 공항동·방화1동으로 별도 비교한다.
core_magok = ['발산1동', '가양1동']
airport_adjacent = ['공항동', '방화1동']
gangseo_total_name = '서울특별시강서구(1150000000)'

latest_period = int(df['period'].max())
base_period = int(df['period'].min())
latest = df[df['period'] == latest_period].copy()
base = df[df['period'] == base_period].copy()

# 동별 변화표
rows = []
for dong in sorted([x for x in latest['admin_dong_norm'].dropna().unique() if x != gangseo_total_name]):
    l = latest[latest['admin_dong_norm'] == dong].iloc[0]
    b = base[base['admin_dong_norm'] == dong].iloc[0]
    rows.append({
        'admin_dong': dong,
        'zone_type': '마곡핵심권' if dong in core_magok else ('공항연계권' if dong in airport_adjacent else '강서기타'),
        'population_2019': b['resident_population'],
        'population_latest': l['resident_population'],
        'population_change_pct': pct_change(l['resident_population'], b['resident_population']),
        'households_2019': b['households'],
        'households_latest': l['households'],
        'households_change_pct': pct_change(l['households'], b['households']),
        'avg_household_size_2019': b['avg_household_size'],
        'avg_household_size_latest': l['avg_household_size'],
        'avg_household_size_change': l['avg_household_size'] - b['avg_household_size'],
        'share_20_39_2019_pct': b['share_20_39_pct'],
        'share_20_39_latest_pct': l['share_20_39_pct'],
        'share_20_39_change_p': l['share_20_39_pct'] - b['share_20_39_pct'],
        'share_60_plus_latest_pct': l['share_60_plus_pct'],
    })
dong_change = pd.DataFrame(rows)

gangseo_l = latest[latest['admin_dong_norm'] == gangseo_total_name].iloc[0]
gangseo_b = base[base['admin_dong_norm'] == gangseo_total_name].iloc[0]

def aggregate_zone(dongs, label):
    sub_l = latest[latest['admin_dong_norm'].isin(dongs)]
    sub_b = base[base['admin_dong_norm'].isin(dongs)]
    pop_l, pop_b = sub_l['resident_population'].sum(), sub_b['resident_population'].sum()
    hh_l, hh_b = sub_l['households'].sum(), sub_b['households'].sum()
    y_l, y_b = sub_l['pop_20_39'].sum(), sub_b['pop_20_39'].sum()
    old_l = sub_l['pop_60_plus'].sum()
    return {
        'comparison_unit': label,
        'population_2019': pop_b,
        'population_latest': pop_l,
        'population_change_pct': pct_change(pop_l, pop_b),
        'households_2019': hh_b,
        'households_latest': hh_l,
        'households_change_pct': pct_change(hh_l, hh_b),
        'avg_household_size_latest': pop_l / hh_l if hh_l else np.nan,
        'avg_household_size_2019': pop_b / hh_b if hh_b else np.nan,
        'share_20_39_latest_pct': y_l / pop_l * 100 if pop_l else np.nan,
        'share_20_39_2019_pct': y_b / pop_b * 100 if pop_b else np.nan,
        'share_60_plus_latest_pct': old_l / pop_l * 100 if pop_l else np.nan,
    }

comparison = pd.DataFrame([
    aggregate_zone(core_magok, '마곡핵심권(발산1동+가양1동)'),
    aggregate_zone(airport_adjacent, '공항연계권(공항동+방화1동)'),
    {
        'comparison_unit': '강서구 전체',
        'population_2019': gangseo_b['resident_population'],
        'population_latest': gangseo_l['resident_population'],
        'population_change_pct': pct_change(gangseo_l['resident_population'], gangseo_b['resident_population']),
        'households_2019': gangseo_b['households'],
        'households_latest': gangseo_l['households'],
        'households_change_pct': pct_change(gangseo_l['households'], gangseo_b['households']),
        'avg_household_size_latest': gangseo_l['avg_household_size'],
        'avg_household_size_2019': gangseo_b['avg_household_size'],
        'share_20_39_latest_pct': gangseo_l['share_20_39_pct'],
        'share_20_39_2019_pct': gangseo_b['share_20_39_pct'],
        'share_60_plus_latest_pct': gangseo_l['share_60_plus_pct'],
    },
    # 2026년 4월 주민등록 인구통계 페이지에서 확인한 서울 현재화면 값. 세대원수별 세대수 기준이므로 1인세대 비교 보조지표로만 사용한다.
    {
        'comparison_unit': '서울 전체(2026.04 주민등록 세대)',
        'population_2019': np.nan,
        'population_latest': np.nan,
        'population_change_pct': np.nan,
        'households_2019': np.nan,
        'households_latest': 4521744,
        'households_change_pct': np.nan,
        'avg_household_size_latest': np.nan,
        'avg_household_size_2019': np.nan,
        'share_20_39_latest_pct': np.nan,
        'share_20_39_2019_pct': np.nan,
        'share_60_plus_latest_pct': np.nan,
        'one_person_households_latest': 2049061,
        'one_person_household_share_latest_pct': 2049061 / 4521744 * 100,
    }
])
comparison['share_20_39_change_p'] = comparison['share_20_39_latest_pct'] - comparison['share_20_39_2019_pct']
comparison['avg_household_size_change'] = comparison['avg_household_size_latest'] - comparison['avg_household_size_2019']

# 동별 순위: 20~39세 비중, 평균 가구원수 낮음, 가구 증가율, 인구 증가율
dong_rank = dong_change.copy()
for col, asc in [('share_20_39_latest_pct', False), ('avg_household_size_latest', True), ('households_change_pct', False), ('population_change_pct', False)]:
    dong_rank[col + '_rank'] = dong_rank[col].rank(ascending=asc, method='min')
dong_rank['magok_single_young_signal_score'] = (
    (21 - dong_rank['share_20_39_latest_pct_rank']) * 0.35 +
    (21 - dong_rank['avg_household_size_latest_rank']) * 0.30 +
    (21 - dong_rank['households_change_pct_rank']) * 0.20 +
    (21 - dong_rank['population_change_pct_rank']) * 0.15
)
dong_rank = dong_rank.sort_values('magok_single_young_signal_score', ascending=False)

# 저장
for path, data in [
    (OUT / 'magok_demographic_specificity_by_dong.csv', dong_change),
    (OUT / 'magok_demographic_specificity_comparison.csv', comparison),
    (OUT / 'magok_young_single_household_signal_rank.csv', dong_rank),
]:
    data.to_csv(path, index=False, encoding='utf-8-sig')

# 시각화 1: 20~39세 비중 vs 평균가구원수
plot_df = dong_change.copy()
colors = plot_df['zone_type'].map({'마곡핵심권':'#d62728','공항연계권':'#ff7f0e','강서기타':'#7f7f7f'})
plt.figure(figsize=(10, 7))
plt.scatter(plot_df['avg_household_size_latest'], plot_df['share_20_39_latest_pct'], s=plot_df['households_latest']/120, c=colors, alpha=0.75, edgecolor='white')
for _, r in plot_df.iterrows():
    if r['zone_type'] != '강서기타' or r['share_20_39_latest_pct'] >= 40 or r['avg_household_size_latest'] <= 1.9:
        plt.text(r['avg_household_size_latest']+0.01, r['share_20_39_latest_pct']+0.15, r['admin_dong'], fontsize=9)
plt.axhline(gangseo_l['share_20_39_pct'], color='black', linestyle='--', linewidth=1, label='강서구 20~39세 비중')
plt.axvline(gangseo_l['avg_household_size'], color='black', linestyle=':', linewidth=1, label='강서구 평균 가구원수')
plt.xlabel('최신 평균 가구원수: 낮을수록 1인·소가구 신호')
plt.ylabel('20~39세 인구 비중(%)')
plt.title('마곡권의 청년·소가구 특수성: 강서구 행정동 비교')
plt.legend()
plt.tight_layout()
plt.savefig(FIG / 'magok_young_single_household_specificity_scatter.png', dpi=180)
plt.close()

# 시각화 2: 권역 비교 변화율
comp_plot = comparison[comparison['comparison_unit'].isin(['마곡핵심권(발산1동+가양1동)','공항연계권(공항동+방화1동)','강서구 전체'])].copy()
labels = comp_plot['comparison_unit'].str.replace('(', '\n(', regex=False)
x = np.arange(len(labels))
width = 0.35
plt.figure(figsize=(10, 6))
plt.bar(x-width/2, comp_plot['population_change_pct'], width, label='인구 변화율')
plt.bar(x+width/2, comp_plot['households_change_pct'], width, label='가구 변화율')
plt.axhline(0, color='black', linewidth=0.8)
plt.xticks(x, labels, rotation=0)
plt.ylabel('2019→2026 변화율(%)')
plt.title('마곡핵심권은 인구보다 가구 변화가 중요한지 검증')
plt.legend()
plt.tight_layout()
plt.savefig(FIG / 'magok_population_household_change_comparison.png', dpi=180)
plt.close()

# 해석 메모
core = comparison.loc[comparison['comparison_unit']=='마곡핵심권(발산1동+가양1동)'].iloc[0]
air = comparison.loc[comparison['comparison_unit']=='공항연계권(공항동+방화1동)'].iloc[0]
seoul_one_share = 2049061 / 4521744 * 100
notes = f"""# 마곡 특수성 1차 검증: 인구·가구 구조

이 문서는 기존 결론을 보류하고, **마곡이어야 하는 이유**를 먼저 검증하기 위한 인구·가구 분석 결과이다. 현재 보유 패널은 강서구 행정동 단위 2019년 12월부터 2026년 4월까지의 주민등록 인구·세대·연령 구조 자료이며, 마곡동은 별도 행정동이 아니므로 **발산1동과 가양1동을 마곡핵심권**으로 묶어 분석했다. 공항 접근성과 항공 관련 생활수요는 **공항동과 방화1동을 공항연계권**으로 분리해 비교했다.

## 핵심 수치

| 비교 단위 | 2019 인구 | 최신 인구 | 인구 변화율 | 2019 가구 | 최신 가구 | 가구 변화율 | 최신 평균 가구원수 | 최신 20~39세 비중 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 마곡핵심권 | {core['population_2019']:.0f} | {core['population_latest']:.0f} | {core['population_change_pct']:.2f}% | {core['households_2019']:.0f} | {core['households_latest']:.0f} | {core['households_change_pct']:.2f}% | {core['avg_household_size_latest']:.2f} | {core['share_20_39_latest_pct']:.2f}% |
| 공항연계권 | {air['population_2019']:.0f} | {air['population_latest']:.0f} | {air['population_change_pct']:.2f}% | {air['households_2019']:.0f} | {air['households_latest']:.0f} | {air['households_change_pct']:.2f}% | {air['avg_household_size_latest']:.2f} | {air['share_20_39_latest_pct']:.2f}% |
| 강서구 전체 | {gangseo_b['resident_population']:.0f} | {gangseo_l['resident_population']:.0f} | {pct_change(gangseo_l['resident_population'], gangseo_b['resident_population']):.2f}% | {gangseo_b['households']:.0f} | {gangseo_l['households']:.0f} | {pct_change(gangseo_l['households'], gangseo_b['households']):.2f}% | {gangseo_l['avg_household_size']:.2f} | {gangseo_l['share_20_39_pct']:.2f}% |
| 서울 전체 보조지표 | NA | NA | NA | NA | 4,521,744 | NA | NA | 1인세대 비중 {seoul_one_share:.2f}% |

## 현재까지 확인된 인사이트

마곡핵심권은 단순히 유동인구가 많은 역세권이라는 이유만으로 설명하면 부족하다. 행정동 패널에서 확인할 수 있는 첫 번째 특수성은 **20~39세 비중과 소가구 신호가 강서구 평균과 다르게 나타나는지**이다. 특히 가양1동은 2019년부터 이미 평균 가구원수가 낮고 20~39세 비중이 높은 편이어서, 마곡 업무·주거 복합지의 1인 생활수요를 설명하는 후보 축으로 볼 수 있다. 발산1동은 마곡나루·마곡역·발산역 생활권과 대학병원 접근성이 겹치는 위치이므로, 다음 단계에서 병원·기업·지하철·공항 데이터를 붙여야 실제 특수성이 확정된다.

서울 전체와의 비교는 현재 주민등록 세대원수별 세대수 페이지에서 2026년 4월 서울 전체 1인세대 비중 {seoul_one_share:.2f}%를 확인한 상태다. 다만 이 값은 행정동 패널의 평균 가구원수·연령구조와 지표 정의가 완전히 같지 않으므로, 최종 보고서에서는 **서울 전체 1인세대 비중은 외부 기준선**, 강서구 행정동 패널은 **마곡 내부 비교의 주자료**로 분리해 사용해야 한다.

## 다음 분석으로 넘길 질문

마곡의 특수성은 인구·가구만으로 끝나지 않는다. 다음 단계에서는 공항 접근성, 이대서울병원·응급 보호자 수요, 마곡 기업 입주와 10년 변화, 편의점 위층 공공시설로 연결 가능한 야간·교대·대기 수요를 각각 별도 데이터로 검증해야 한다. 이번 산출물은 그중 첫 단계로, **마곡핵심권이 서울·강서구 평균과 다른 생활권인지 확인하는 기초 비교표와 Tableau용 데이터** 역할을 한다.

## 산출 파일

| 파일 | 용도 |
|---|---|
| `magok_demographic_specificity_by_dong.csv` | 강서구 행정동별 2019→2026 인구·가구·연령 변화 Tableau 원자료 |
| `magok_demographic_specificity_comparison.csv` | 마곡핵심권·공항연계권·강서구·서울 보조지표 비교표 |
| `magok_young_single_household_signal_rank.csv` | 청년·소가구 신호 기준 행정동 순위 |
| `figures/magok_young_single_household_specificity_scatter.png` | 20~39세 비중 × 평균 가구원수 비교 시각화 |
| `figures/magok_population_household_change_comparison.png` | 마곡핵심권·공항연계권·강서구 변화율 비교 시각화 |
"""
(OUT / 'magok_demographic_specificity_findings.md').write_text(notes, encoding='utf-8')

print('latest_period', latest_period)
print('wrote demographic specificity outputs to', OUT)
print(comparison.to_string(index=False))
print('\nTop signal dongs:')
print(dong_rank[['admin_dong','zone_type','share_20_39_latest_pct','avg_household_size_latest','households_change_pct','magok_single_young_signal_score']].head(10).to_string(index=False))
