import pandas as pd
from pathlib import Path
p=Path('/home/ubuntu/data_final_analysis_work/reanalysis/inputs/gangseo_demographics_by_dong_period.csv')
df=pd.read_csv(p)
print('shape', df.shape)
print('years', sorted(df['year'].dropna().unique().tolist()))
print('dongs', sorted(df['admin_dong_norm'].dropna().unique().tolist()))
print(df[df['admin_dong_norm'].astype(str).str.contains('마곡|발산|가양|공항', regex=True, na=False)].tail(30).to_string(index=False))
