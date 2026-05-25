from pathlib import Path
import pandas as pd

path = Path('/home/ubuntu/data_final_analysis_work/reanalysis/raw/gangseo_one_person_households_20250731.xlsx')
xl = pd.ExcelFile(path)
print('sheets:', xl.sheet_names)
for sheet in xl.sheet_names:
    print('\n---', sheet, '---')
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    print(df.shape)
    print(df.head(15).to_string(index=False))
