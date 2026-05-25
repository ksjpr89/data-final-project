from pathlib import Path
import pandas as pd
import json

base = Path('/home/ubuntu/data_final_analysis_work/expanded_inputs')
files = sorted(base.glob('*'))
rows=[]
for p in files:
    info={'file':p.name,'size':p.stat().st_size}
    try:
        if p.suffix.lower()=='.csv':
            for enc in ['utf-8-sig','cp949','euc-kr','utf-8']:
                try:
                    df=pd.read_csv(p, nrows=5, encoding=enc)
                    info['encoding']=enc
                    info['shape_sample']=df.shape
                    info['columns']=list(map(str,df.columns))
                    info['sample']=df.head(2).astype(str).to_dict(orient='records')
                    break
                except Exception as e:
                    last=str(e)
            else:
                info['error']=last
        elif p.suffix.lower() in ['.xlsx','.xls']:
            xl=pd.ExcelFile(p)
            info['sheets']=xl.sheet_names
            sample={}
            for s in xl.sheet_names[:5]:
                df=pd.read_excel(p, sheet_name=s, nrows=5)
                sample[s]={'columns':list(map(str,df.columns)), 'head':df.head(2).astype(str).to_dict(orient='records')}
            info['sample']=sample
    except Exception as e:
        info['error']=repr(e)
    rows.append(info)
out = Path('/home/ubuntu/data_final_analysis_work/outputs/expanded_input_audit.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
