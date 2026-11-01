"""Run from project root: python -m uvicorn backend.main:app --port 8000"""
import csv
import io
import json
from contextlib import closing
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from backend.analytics import connect, metadata, params_for, dashboard, query
from backend.pipeline import ROOT

app=FastAPI(title='CommerceLens Analytics',version='1.0.0')

@app.get('/api/health')
def health():
    try:
        with closing(connect()) as c:
            c.execute('SELECT COUNT(*) FROM order_facts').fetchone()
        return {'status':'ok'}
    except FileNotFoundError as e: raise HTTPException(503,str(e))

@app.get('/api/dashboard')
def get_dashboard(start: str|None=None,end: str|None=None,category: str='',state: str=''):
    try:
        with closing(connect()) as c:
            return dashboard(c,params_for(metadata(c),start,end,category,state))
    except ValueError as e: raise HTTPException(422,str(e))
    except FileNotFoundError as e: raise HTTPException(503,str(e))

@app.get('/api/methodology')
def methodology():
    return json.loads((ROOT/'docs/metrics.json').read_text(encoding='utf-8'))

@app.get('/api/export/{table}')
def export(table: str,start: str|None=None,end: str|None=None,category: str='',state: str=''):
    if table not in ['categories','regions','monthly','frequency','delivery','reviews','cohorts']:
        raise HTTPException(404,'Unknown export table')
    try:
        with closing(connect()) as c:
            meta=metadata(c)
            params=params_for(meta,start,end,category,state)
            if table=='cohorts': params['end']=min(params['end'],meta['end'])
            rows=query(c,table,params)
        out=io.StringIO(newline='')
        if rows:
            writer=csv.DictWriter(out,fieldnames=list(rows[0])+['data_source','filter_start','filter_end','filter_category','filter_state'])
            writer.writeheader()
            for row in rows:
                # Prevent spreadsheet formulas in externally supplied dimension labels.
                safe={k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for k,v in row.items()}
                writer.writerow({**safe,'data_source':meta['source'],'filter_start':params['start'],'filter_end':params['end'],
                                 'filter_category':'Not applied' if table=='cohorts' else category,
                                 'filter_state':'Not applied' if table=='cohorts' else state})
        else: out.write('data_source\r\n'+meta['source']+'\r\n')
        return Response('\ufeff'+out.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="commercelens-{table}.csv"'})
    except ValueError as e: raise HTTPException(422,str(e))
    except FileNotFoundError as e: raise HTTPException(503,str(e))
