from pathlib import Path
import pandas as pd

path = Path('/home/ubuntu/data_final_analysis_work/expanded_inputs/gangseo_business_report_2023_based_20250731.xlsx')
for sheet in ['1.산업대분류별 동별 총괄','2.산업세세분류별 동별 현황']:
    print('\nSHEET', sheet)
    df = pd.read_excel(path, sheet_name=sheet, header=None, nrows=20)
    pd.set_option('display.max_columns', 60)
    print(df.iloc[:12, :45].to_string())
