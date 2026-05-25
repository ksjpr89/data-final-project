from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path('/home/ubuntu/data_final_analysis_work/outputs')
FIG = BASE / 'figures'
FIG.mkdir(exist_ok=True)

change = pd.read_csv(BASE / 'candidate_change_summary_2019_2025.csv')
lm = pd.read_csv(BASE / 'candidate_living_movement_avg_daily_direction.csv')
panel = pd.read_csv(BASE / 'candidate_store_demographic_panel_2019_2025.csv')

# 1. Store and population change bar chart
plot = change.sort_values('total_store_change_pct', ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(plot['admin_dong_norm'], plot['total_store_change_pct'], color='#4C78A8', label='Store count change')
ax.scatter(plot['population_change_pct'], plot['admin_dong_norm'], color='#F58518', label='Population change', zorder=3)
ax.axvline(0, color='gray', linewidth=0.8)
ax.set_xlabel('Change from 2019 to 2025 (%)')
ax.set_ylabel('Candidate administrative dong')
ax.set_title('Candidate Areas: Store Growth vs Resident Population Change, 2019-2025')
ax.legend(loc='lower right')
fig.tight_layout()
fig.savefig(FIG / 'candidate_store_vs_population_change_2019_2025.png', dpi=180)
plt.close(fig)

# 2. Convenience stores per 1,000 residents in 2025
plot = change.sort_values('convenience_per_1000_last', ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(plot['admin_dong_norm'], plot['convenience_per_1000_last'], color='#54A24B')
ax.set_xlabel('Convenience stores per 1,000 residents, 2025')
ax.set_ylabel('Candidate administrative dong')
ax.set_title('Convenience Store Density by Candidate Area')
fig.tight_layout()
fig.savefig(FIG / 'candidate_convenience_density_2025.png', dpi=180)
plt.close(fig)

# 3. Living movement inbound average daily count
inbound = lm[lm['direction'] == 'inbound_to_candidate'].sort_values('movement_population', ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(inbound['candidate_dong'], inbound['movement_population'], color='#B279A2')
ax.set_xlabel('Average daily inbound movement population, representative days')
ax.set_ylabel('Candidate administrative dong')
ax.set_title('Representative Inbound Living Movement, 2026-03-28 to 2026-03-31')
fig.tight_layout()
fig.savefig(FIG / 'candidate_inbound_living_movement_20260328_31.png', dpi=180)
plt.close(fig)

# Compact ranked table
rank = change.copy()
rank['rank_store_growth'] = rank['total_store_change_pct'].rank(ascending=False, method='min').astype(int)
rank['rank_convenience_density'] = rank['convenience_per_1000_last'].rank(ascending=False, method='min').astype(int)
inbound_map = inbound.set_index('candidate_dong')['movement_population']
rank['avg_daily_inbound_movement_20260328_31'] = rank['admin_dong_norm'].map(inbound_map)
rank['rank_inbound_movement'] = rank['avg_daily_inbound_movement_20260328_31'].rank(ascending=False, method='min').astype(int)
rank = rank[['admin_dong_norm','rank_store_growth','total_store_change_pct','population_change_pct','convenience_change_pct','convenience_per_1000_last','avg_daily_inbound_movement_20260328_31','rank_convenience_density','rank_inbound_movement','share_20_39_last','share_60_plus_last']]
rank.to_csv(BASE / 'candidate_preliminary_ranking_summary.csv', index=False, encoding='utf-8-sig')

with pd.ExcelWriter(BASE / 'candidate_preliminary_analysis_tables.xlsx', engine='openpyxl') as writer:
    change.to_excel(writer, sheet_name='change_2019_2025', index=False)
    panel.to_excel(writer, sheet_name='panel_2019_2025', index=False)
    lm.to_excel(writer, sheet_name='living_movement_avg', index=False)
    rank.to_excel(writer, sheet_name='preliminary_ranking', index=False)

print('created figures and excel outputs')
