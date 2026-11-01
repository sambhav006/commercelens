"""Inspect headers, retain raw data, clean, validate and atomically rebuild SQLite."""
import argparse
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from backend.demo import FILES, generate

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'commerce.sqlite'
REQUIRED = {
 'orders': ['order_id','customer_id','order_status','order_purchase_timestamp','order_delivered_customer_date','order_estimated_delivery_date'],
 'items': ['order_id','order_item_id','product_id','price','freight_value'],
 'customers': ['customer_id','customer_unique_id','customer_state'],
 'products': ['product_id','product_category_name'],
 'translations': ['product_category_name','product_category_name_english'],
 'payments': ['order_id','payment_sequential','payment_value'],
 'reviews': ['review_id','order_id','review_score','review_answer_timestamp'],
}
KEYS = {'orders':['order_id'], 'items':['order_id','order_item_id'], 'customers':['customer_id'],
        'products':['product_id'], 'translations':['product_category_name'],
        'payments':['order_id','payment_sequential'], 'reviews':['review_id','order_id']}

def inspect(folder):
    result = {}
    for name, filename in FILES.items():
        path = folder / filename
        if not path.exists(): raise ValueError(f'Missing required file: {path.name}. Supply all seven CSVs.')
        columns = pd.read_csv(path, nrows=0).columns.tolist()
        missing = sorted(set(REQUIRED[name])-set(columns))
        if missing: raise ValueError(f'{filename}: missing columns {missing}; observed {columns}')
        result[name] = columns
    return result

def ingest(folder=None, db=DB, mode=None):
    folder = Path(folder) if folder else ROOT/'data'/'raw'
    if mode == 'demo' or (mode is None and not any(folder.glob('*.csv'))):
        folder = generate(ROOT/'data'/'demo')
        mode = 'synthetic'
    else:
        mode = mode or 'real'
    columns = inspect(folder)  # Validate actual headers before transformations.
    report, frames, raw = {}, {}, {}
    for name, filename in FILES.items():
        f = pd.read_csv(folder/filename, dtype='string')
        raw[name] = f.copy()
        f = f.apply(lambda s: s.str.strip().replace('', pd.NA))
        r = {'raw_rows':len(f),'columns':columns[name], 'missing_values':{c:int(v) for c,v in f.isna().sum().items()},
             'duplicates':int(f.duplicated(KEYS[name]).sum()), 'invalid_values':{}, 'orphans':{}, 'excluded':{}}
        bad = f[KEYS[name]].isna().any(axis=1)
        r['excluded']['missing_key'] = int(bad.sum())
        f = f.loc[~bad].copy()
        # Stable input order breaks ties. Review answer timestamps are ranked again in SQL.
        if name == 'reviews': f = f.sort_values('review_answer_timestamp', kind='stable', na_position='first')
        f = f.drop_duplicates(KEYS[name], keep='last')
        for c in [c for c in f if c.endswith('_timestamp') or c.endswith('_date')]:
            parsed = pd.to_datetime(f[c], errors='coerce', format='mixed')
            r['invalid_values'][c] = int((f[c].notna() & parsed.isna()).sum())
            f[c] = parsed.dt.strftime('%Y-%m-%d %H:%M:%S').where(parsed.notna(), None)
        for c in [c for c in ['price','freight_value','payment_value','review_score','order_item_id','payment_sequential'] if c in f]:
            num = pd.to_numeric(f[c],errors='coerce').astype(float)
            valid = np.isfinite(num) & (num >= 0)
            if c in ['order_item_id','payment_sequential']: valid &= (num >= 1) & (num % 1 == 0)
            if c == 'review_score': valid &= num.between(1,5) & (num % 1 == 0)
            r['invalid_values'][c] = int((~valid & f[c].notna()).sum())
            f[c] = num.where(valid, np.nan)
        if name == 'orders':
            bad = f.order_purchase_timestamp.isna()
            r['excluded']['invalid_purchase_date'] = int(bad.sum())
            f = f.loc[~bad].copy()
            f['order_status'] = f.order_status.fillna('unknown').str.lower()
            purchase = pd.to_datetime(f.order_purchase_timestamp)
            for c in ['order_delivered_customer_date','order_estimated_delivery_date']:
                invalid = pd.to_datetime(f[c]).dt.normalize() < purchase.dt.normalize()
                r['invalid_values'][c+'_before_purchase'] = int(invalid.sum())
                f.loc[invalid,c] = None
        if name in ['items','payments']:
            bad = f[KEYS[name]].isna().any(axis=1)
            r['excluded']['invalid_sequence'] = int(bad.sum())
            f = f.loc[~bad].copy()
            f = f.drop_duplicates(KEYS[name],keep='last')
        if name == 'customers':
            f['customer_state'] = f.customer_state.str.upper().fillna('Unknown')
        frames[name] = f
        report[name] = r
    # Orphan dimensions are retained as Unknown; orphan child facts cannot be attributed.
    for child, key, parent, pkey, drop in [
        ('orders','customer_id','customers','customer_id',False),
        ('items','order_id','orders','order_id',True),
        ('items','product_id','products','product_id',False),
        ('payments','order_id','orders','order_id',True),
        ('reviews','order_id','orders','order_id',True),
        ('products','product_category_name','translations','product_category_name',False)]:
        bad = ~frames[child][key].isin(frames[parent][pkey])
        report[child]['orphans'][key] = int(bad.sum())
        if drop:
            report[child]['excluded']['orphan_'+key] = int(bad.sum())
            frames[child] = frames[child].loc[~bad].copy()
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    temp = db.with_suffix('.building.sqlite')
    if temp.exists(): temp.unlink()
    try:
        with closing(sqlite3.connect(temp)) as conn:
            for name in FILES:
                raw[name].to_sql('raw_'+name,conn,index=False,if_exists='replace')
                frames[name].to_sql(name,conn,index=False,if_exists='replace')
                keys = ','.join(KEYS[name])
                conn.execute(f'CREATE UNIQUE INDEX pk_{name} ON {name} ({keys})')
                report[name]['clean_rows'] = len(frames[name])
                report[name]['excluded_rows'] = len(raw[name])-len(frames[name])
                report[name]['primary_key_unique'] = not frames[name].duplicated(KEYS[name]).any().item()
            conn.executescript((ROOT/'backend/sql/model.sql').read_text())
            bounds = conn.execute('SELECT MIN(purchase_date),MAX(purchase_date) FROM order_facts').fetchone()
            if not bounds[0]: raise ValueError('No valid orders remain after cleaning.')
            checks = dict(conn.execute('''SELECT 'orders_without_complete_item_prices', COUNT(*) FROM order_facts WHERE sales_eligible=0
                UNION ALL SELECT 'delivered_missing_delivery_dates',COUNT(*) FROM order_facts WHERE status='delivered' AND late IS NULL
                UNION ALL SELECT 'orders_missing_customer_identity',COUNT(*) FROM order_facts WHERE customer_unique_id IS NULL
                UNION ALL SELECT 'orders_with_multiple_reviews',COUNT(*) FROM (SELECT order_id FROM reviews GROUP BY order_id HAVING COUNT(*)>1)''').fetchall())
            meta = {'mode':mode,'source':'Synthetic demo data' if mode=='synthetic' else 'Olist local CSV files',
                    'start':bounds[0],'end':bounds[1], 'ingested_at':datetime.now(timezone.utc).isoformat(),
                    'tables':report,'checks':checks,'seed':42 if mode=='synthetic' else None}
            conn.execute('CREATE TABLE metadata (payload TEXT NOT NULL)')
            conn.execute('INSERT INTO metadata VALUES (?)',(json.dumps(meta),))
            conn.commit()
        os.replace(temp,db)
    except Exception:
        if temp.exists(): temp.unlink()
        raise
    return meta

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path)
    p.add_argument('--mode',choices=['auto','demo','real'],default='auto')
    p.add_argument('--inspect',action='store_true')
    a=p.parse_args()
    if a.inspect: print(json.dumps(inspect(a.source or ROOT/'data/raw'),indent=2))
    else:
        m=ingest(a.source,mode=None if a.mode=='auto' else a.mode)
        print(json.dumps(m,indent=2))
