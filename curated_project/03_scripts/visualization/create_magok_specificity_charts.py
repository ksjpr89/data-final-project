from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
FIG = OUT / 'figures'
FIG.mkdir(parents=True, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')

# Korean font fallback: apply after style so the style does not override the font.
font_candidates = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf',
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
]
for fp in font_candidates:
    if Path(fp).exists():
        font_manager.fontManager.addfont(fp)
        rcParams['font.family'] = font_manager.FontProperties(fname=fp).get_name()
        break
rcParams['axes.unicode_minus'] = False

airport = pd.read_csv(OUT / 'kac_gimpo_airport_passenger_summary_2016_2025.csv')
fig, ax1 = plt.subplots(figsize=(10,5.6), dpi=180)
ax1.plot(airport['year'], airport['gimpo_passenger_total']/1_000_000, marker='o', linewidth=2.5, color='#1f77b4', label='총여객')
ax1.plot(airport['year'], airport['gimpo_domestic_passenger']/1_000_000, marker='o', linewidth=2, color='#2ca02c', label='국내선')
ax1.plot(airport['year'], airport['gimpo_international_passenger']/1_000_000, marker='o', linewidth=2, color='#ff7f0e', label='국제선')
ax1.set_title('김포공항 여객 추이: 마곡 인근 공항 거점성의 절대 규모', fontsize=14, pad=14, weight='bold')
ax1.set_xlabel('연도')
ax1.set_ylabel('여객 수(백만 명)')
ax1.legend(loc='upper left', frameon=True)
ax1.annotate('2025년 총여객\n2,296만 명', xy=(2025, airport.loc[airport['year']==2025,'gimpo_passenger_total'].iloc[0]/1_000_000), xytext=(2023.35, 25.2), arrowprops=dict(arrowstyle='->', color='#444444', lw=1.2), fontsize=10, ha='left', va='center', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#cccccc', alpha=0.9))
fig.tight_layout()
fig.savefig(FIG / 'gimpo_airport_passenger_trend_2016_2025.png', bbox_inches='tight')
plt.close(fig)

one = pd.read_csv(OUT / 'magok_specificity_one_person_metrics.csv')
bar_data = one[one['metric'].isin(['서울 자치구 평균 1인가구','강서구 1인가구','마곡 관련 후보 행정동 1인가구'])].copy()
fig, ax = plt.subplots(figsize=(8.5,5.2), dpi=180)
colors = ['#9ecae1','#3182bd','#08519c']
ax.bar(bar_data['metric'], bar_data['value'], color=colors)
ax.set_title('1인가구 규모 비교: 강서구와 마곡 관련 후보권역', fontsize=14, pad=14, weight='bold')
ax.set_ylabel('1인가구 수(가구)')
ax.tick_params(axis='x', rotation=15)
for i, v in enumerate(bar_data['value']):
    ax.text(i, v*1.01, f'{int(v):,}', ha='center', fontsize=10)
fig.tight_layout()
fig.savefig(FIG / 'one_person_household_comparison_2024.png', bbox_inches='tight')
plt.close(fig)

hyp = pd.read_csv(OUT / 'magok_specificity_hypothesis_evidence_matrix.csv')
level_map = {'중': 2, '중상': 3, '상': 4}
hyp['score'] = hyp['evidence_level'].map(level_map)
fig, ax = plt.subplots(figsize=(10,5.8), dpi=180)
hyp_plot = hyp.sort_values('score')
ax.barh(hyp_plot['hypothesis'], hyp_plot['score'], color=['#fdd0a2' if x==2 else '#74c476' if x==3 else '#238b45' for x in hyp_plot['score']])
ax.set_xlim(0,4.5)
ax.set_xlabel('근거 강도 점수(중=2, 중상=3, 상=4)')
ax.set_title('마곡 특수성 가설별 현재 근거 강도', fontsize=14, pad=14, weight='bold')
for y, (score, level) in enumerate(zip(hyp_plot['score'], hyp_plot['evidence_level'])):
    ax.text(score + 0.08, y, level, va='center', fontsize=10)
fig.tight_layout()
fig.savefig(FIG / 'magok_hypothesis_evidence_strength.png', bbox_inches='tight')
plt.close(fig)

print('saved charts:')
for p in sorted(FIG.glob('*specificity*png')) + sorted(FIG.glob('gimpo_airport_passenger_trend_2016_2025.png')) + sorted(FIG.glob('one_person_household_comparison_2024.png')):
    print(p)
