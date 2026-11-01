import csv
import io
import sqlite3
from contextlib import closing
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.demo import FILES, generate
from backend.pipeline import ingest, inspect
from backend.analytics import connect, metadata, params_for, dashboard, query
from backend import main

@pytest.fixture
def dataset(tmp_path):
    folder=tmp_path/'csv'
    folder.mkdir()
    rows={
      'orders':[
       ['o1','c1','delivered','2024-01-01 10:00:00','2024-01-05 23:00:00','2024-01-05 00:00:00'],
       ['o2','c2','delivered','2024-02-02','2024-02-10','2024-02-08'],
       ['o3','c3','canceled','2024-02-03',None,'2024-02-20'],
       ['o4','c4','delivered','2024-02-04',None,'2024-02-20'],
       ['o5','c5','delivered','2024-03-15','2024-03-20','2024-03-22'],
       ['o6','c6','delivered','2024-01-12','2024-01-15','2024-01-17']],
      'customers':[['c1','same_person','SP'],['c2','same_person','SP'],['c3','canceled_person','RJ'],
                   ['c4','missing_dates_person','RJ'],['c5','march_person','SP'],['c6','january_person','RJ']],
      'items':[['o1',1,'p1',100,10],['o1',2,'p2',50,5],['o2',1,'p2',80,8],['o3',1,'p1',999,10],
               ['o4',1,'p1',20,3],['o5',1,'p2',40,4],['o6',1,'p1',10,2]],
      'products':[['p1','a'],['p2','b']],
      'translations':[['a','alpha'],['b','beta']],
      'payments':[['o1',1,100],['o1',2,65],['o2',1,88]],
      'reviews':[['r1','o1',1,'2024-01-06'],['r2','o1',5,'2024-01-07'],['r3','o2',2,'2024-02-11']],
    }
    from backend.pipeline import REQUIRED
    for name,values in rows.items(): pd.DataFrame(values,columns=REQUIRED[name]).to_csv(folder/FILES[name],index=False)
    db=tmp_path/'test.sqlite'
    ingest(folder,db,mode='synthetic')
    return folder,db

def get(db,**filters):
    with closing(connect(db)) as c:return dashboard(c,params_for(metadata(c),**filters))

def test_grains_statuses_and_identity(dataset):
    _,db=dataset
    k=get(db)['kpis']
    assert k['sales']==300  # 150+80+20+40+10; canceled 999 never included
    assert k['aov']==60
    assert k['placed_orders']==6
    assert k['cancellation_rate']==pytest.approx(1/6)
    assert k['customers']==4  # c1 and c2 are the same customer_unique_id
    assert k['repeat_customers']==1
    assert k['repeat_rate']==.25
    assert k['late_rate']==.25  # 1 late / 4 valid dates, not /5 delivered
    assert k['delivery_sample']==4
    with closing(connect(db)) as c:
        o=dict(c.execute("SELECT * FROM order_facts WHERE order_id='o1'").fetchone())
    assert o['item_sales']==150 and o['payment_count']==2 and o['review_score']==5
    assert o['late']==0  # Same calendar day, different hours

def test_category_item_scope_and_cohort_history(dataset):
    _,db=dataset
    d=get(db,category='beta')
    assert d['kpis']['sales']==170
    assert d['kpis']['aov']==pytest.approx(170/3)
    assert sum(r['sales'] for r in d['categories'])==170
    assert d['cohorts']==get(db)['cohorts']  # category never moves first purchase
    assert d['cohorts']==get(db,state='SP')['cohorts']
    jan=[r for r in d['cohorts'] if r['cohort']=='2024-01']
    assert jan[0]['cohort_size']==2 and jan[0]['retention']==1
    assert jan[1]['retention']==.5
    assert jan[2]['retention'] is None  # March is incomplete in this dataset
    assert not any(r['cohort']=='2024-03' for r in d['cohorts'])
    feb=get(db,start='2024-02-01',end='2024-02-29',category='beta')
    assert feb['kpis']['repeat_rate']==0
    assert feb['cohorts'][0]['cohort_size']==1  # first-time February customer only

def test_zero_denominators_and_periods(dataset):
    _,db=dataset
    d=get(db,start='2025-01-01',end='2025-01-31')
    for key in ['sales','aov','repeat_rate','cancellation_rate','late_rate']: assert d['kpis'][key] is None
    assert d['kpis']['placed_orders']==0
    d=get(db,start='2024-02-01',end='2024-02-29')
    assert d['comparison']['start']=='2024-01-03'
    assert d['comparison']['end']=='2024-01-31'
    assert d['comparison']['changes']['sales']==9  # 100 vs 10
    assert d['comparison']['changes']['cancellation_rate'] is None # zero baseline
    assert get(db)['comparison']['changes']['sales'] is None

def test_api_exports_reconcile_and_validation(dataset,monkeypatch):
    _,db=dataset
    monkeypatch.setattr(main,'connect',lambda:connect(db))
    client=TestClient(main.app)
    filters={'start':'2024-01-01','end':'2024-03-15','category':'beta','state':'SP'}
    response=client.get('/api/dashboard',params=filters)
    assert response.status_code==200
    d=response.json()
    for table in ['categories','regions','monthly']:
        r=client.get('/api/export/'+table,params=filters)
        assert r.status_code==200
        rows=list(csv.DictReader(io.StringIO(r.text.lstrip('\ufeff'))))
        assert sum(float(row['sales']) for row in rows)==d['kpis']['sales']
        assert all(row['data_source']=='Synthetic demo data' for row in rows)
        assert all(row['filter_category']=='beta' for row in rows)
    assert client.get('/api/dashboard',params={'start':'nope'}).status_code==422
    assert client.get('/api/dashboard',params={'start':'2024-05-01','end':'2024-01-01'}).status_code==422
    assert client.get('/api/dashboard',params={'category':"' OR 1=1 --"}).status_code==422
    assert client.get('/api/export/not_a_table').status_code==404
    assert client.get('/api/health').status_code==200

def test_quality_exclusions_and_atomic_failure(dataset):
    folder,db=dataset
    items=pd.read_csv(folder/FILES['items'])
    items.loc[(items.order_id=='o1') & (items.order_item_id==1),'price']=-5
    items=pd.concat([items,items.iloc[[1]],pd.DataFrame([dict(order_id='orphan',order_item_id=1,product_id='p1',price=99,freight_value=1)])])
    items.to_csv(folder/FILES['items'],index=False)
    report=ingest(folder,db,mode='synthetic')
    assert report['tables']['items']['duplicates']==1
    assert report['tables']['items']['orphans']['order_id']==1
    assert report['tables']['items']['invalid_values']['price']==1
    assert get(db)['kpis']['sales']==150  # Entire incomplete-price order excluded
    assert get(db)['kpis']['eligible_delivered_orders']==4
    assert get(db)['kpis']['aov']==37.5
    (folder/FILES['orders']).write_text('wrong_column\nabc\n')
    with pytest.raises(ValueError,match='missing columns'):ingest(folder,db,mode='synthetic')
    assert get(db)['kpis']['sales']==150  # Failed ingest leaves old database intact

def test_demo_reproducible_and_ingestion_idempotent(tmp_path):
    a,b=tmp_path/'a',tmp_path/'b'
    generate(a,count=120);generate(b,count=120)
    for filename in FILES.values():assert (a/filename).read_bytes()==(b/filename).read_bytes()
    assert inspect(a)['orders'][0]=='order_id'
    db=tmp_path/'demo.sqlite'
    ingest(a,db,mode='synthetic');before=get(db)
    ingest(a,db,mode='synthetic');after=get(db)
    assert before['kpis']==after['kpis']
    assert before['meta']['tables']==after['meta']['tables']
    assert before['categories']==after['categories']

def test_observed_zero_vs_unobserved(dataset):
    _,db=dataset
    d=get(db,end='2024-03-15')
    feb=[r for r in d['cohorts'] if r['cohort']=='2024-02']
    assert feb[0]['retention']==1
    assert feb[1]['retention'] is None
    with closing(connect(db)) as c:
        p=params_for(metadata(c),end='2024-03-31')
        rows=query(c,'cohorts',p)
    # Isolated SQL query with a declared complete cutoff: zero activity is observed zero.
    assert next(r for r in rows if r['cohort']=='2024-02' and r['age']==1)['retention']==0

def test_schema_missing_file_is_not_silently_demo(tmp_path):
    folder=tmp_path/'partial';folder.mkdir()
    (folder/FILES['orders']).write_text('order_id\no1\n')
    with pytest.raises(ValueError):ingest(folder,tmp_path/'db.sqlite')
