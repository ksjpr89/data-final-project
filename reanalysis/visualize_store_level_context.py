from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

BASE = Path('/home/ubuntu/data_final_analysis_work/reanalysis')
OUT = BASE / 'outputs'
FIG = OUT / 'figures'
FIG.mkdir(parents=True, exist_ok=True)

font_candidates = [
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
]
selected_font = None
for fp in font_candidates:
    if Path(fp).exists():
        fm.fontManager.addfont(fp)
        selected_font = fm.FontProperties(fname=fp).get_name()
        break
if not selected_font:
    selected_font = 'Droid Sans Fallback'
plt.rcParams['font.family'] = selected_font
plt.rcParams['font.sans-serif'] = [selected_font, 'Droid Sans Fallback', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style='whitegrid', font=selected_font)

context = pd.read_csv(OUT / 'tableau_store_level_context_metrics.csv', encoding='utf-8-sig')
known_top = pd.read_csv(OUT / 'top50_known_chain_store_level_context_candidates.csv', encoding='utf-8-sig')
admin = pd.read_csv(OUT / 'store_context_summary_by_admin_dong.csv', encoding='utf-8-sig')

# 1. 강서구 편의점 전체 분포와 상위 후보 위치
plt.figure(figsize=(10, 8))
for brand, g in context.groupby('brand'):
    alpha = 0.45 if brand != '기타/미분류' else 0.20
    plt.scatter(g['longitude'], g['latitude'], s=18, alpha=alpha, label=brand)
plt.scatter(known_top.head(15)['longitude'], known_top.head(15)['latitude'], s=95, facecolors='none', edgecolors='black', linewidths=1.6, label='상위 후보 15개')
for _, r in known_top.head(8).iterrows():
    plt.text(r['longitude'] + 0.0003, r['latitude'] + 0.0002, f"{r['store_name']}\n{r['road_address'].split('강서구 ')[-1]}", fontsize=7)
plt.title('강서구 편의점 분포와 공공시설 후보 점포 상위권 위치')
plt.xlabel('경도')
plt.ylabel('위도')
plt.legend(loc='best', fontsize=8, ncol=2)
plt.tight_layout()
plt.savefig(FIG / 'gangseo_convenience_distribution_top_candidates.png', dpi=220)
plt.close()

# 2. 점포별 유동·의료·접근성 포지셔닝
plt.figure(figsize=(10, 7))
plot_df = context[context['is_known_chain_brand']].copy()
scatter = plt.scatter(
    plot_df['nearest_subway_station_distance_m'],
    plot_df['medical_count_500m'],
    c=plot_df['store_context_exploration_score'],
    s=(plot_df['other_convenience_count_500m'].clip(0, 60) + 5) * 2.2,
    cmap='viridis', alpha=0.65, edgecolors='none'
)
plt.gca().invert_xaxis()
plt.colorbar(scatter, label='점포 컨텍스트 탐색 점수')
plt.title('후보 점포 포지셔닝: 지하철 접근성 × 의료·생활서비스 밀도')
plt.xlabel('가장 가까운 지하철역 거리(m, 왼쪽일수록 가까움)')
plt.ylabel('500m 내 병원·의원 수')
for _, r in known_top.head(8).iterrows():
    plt.text(r['nearest_subway_station_distance_m'] + 8, r['medical_count_500m'] + 1, r['store_name'], fontsize=7)
plt.tight_layout()
plt.savefig(FIG / 'store_context_positioning_scatter.png', dpi=220)
plt.close()

# 3. 행정동별 편의점 수와 최고 후보 점수
admin_top = admin.head(15).copy().sort_values('max_context_score')
fig, ax1 = plt.subplots(figsize=(10, 7))
ax1.barh(admin_top['admin_dong'], admin_top['store_count'], color='#6baed6', alpha=0.8, label='편의점 수')
ax1.set_xlabel('편의점 수')
ax1.set_ylabel('행정동')
ax2 = ax1.twiny()
ax2.plot(admin_top['max_context_score'], admin_top['admin_dong'], color='#de2d26', marker='o', label='최고 후보 점수')
ax2.set_xlabel('행정동 내 최고 점포 탐색 점수')
plt.title('행정동별 편의점 분포와 점포 단위 최고 후보 점수')
fig.tight_layout()
plt.savefig(FIG / 'admin_store_count_and_best_score.png', dpi=220)
plt.close()

# 4. 상위 후보별 구성 점수 비교
profile_cols = ['score_transit_access', 'score_public_health_need', 'score_worker_flow_need', 'score_site_feasibility_pool']
profile_names = {
    'score_transit_access': '대중교통 접근성',
    'score_public_health_need': '생활건강·돌봄 수요',
    'score_worker_flow_need': '직장인·유입수요',
    'score_site_feasibility_pool': '점포밀집·후보풀'
}
prof = known_top.head(10)[['store_name', 'road_address'] + profile_cols].copy()
prof['label'] = prof['store_name'] + '\n' + prof['road_address'].str.replace('서울특별시 강서구 ', '', regex=False)
prof_long = prof.melt(id_vars='label', value_vars=profile_cols, var_name='score_type', value_name='score')
prof_long['score_type'] = prof_long['score_type'].map(profile_names)
plt.figure(figsize=(11, 8))
sns.barplot(data=prof_long, y='label', x='score', hue='score_type')
plt.title('상위 브랜드 확인 가능 후보 점포 10곳의 평가축별 강약점')
plt.xlabel('정규화 점수(0~1)')
plt.ylabel('후보 점포')
plt.legend(title='평가축', loc='lower right')
plt.tight_layout()
plt.savefig(FIG / 'top_known_candidate_score_profiles.png', dpi=220)
plt.close()

print('시각화 생성 완료')
for p in sorted(FIG.glob('*.png')):
    print(p)
