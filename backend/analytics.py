import json
import sqlite3
from datetime import date, timedelta
from backend.pipeline import DB, ROOT

SQL = ROOT/'backend/sql'

def connect(db=DB):
    if not db.exists(): raise FileNotFoundError('Run python -m backend.pipeline before starting the app.')
    conn=sqlite3.connect(db)
    conn.row_factory=sqlite3.Row
    return conn

def metadata(conn):
    m=json.loads(conn.execute('SELECT payload FROM metadata').fetchone()[0])
    m['categories']=[r[0] for r in conn.execute('SELECT DISTINCT category FROM item_facts ORDER BY category')]
    m['states']=[r[0] for r in conn.execute('SELECT DISTINCT state FROM order_facts ORDER BY state')]
    return m

def query(conn, name, params):
    sql=(SQL/f'{name}.sql').read_text()
    if name!='cohorts': sql=(SQL/'scope.sql').read_text()+sql
    return [dict(row) for row in conn.execute(sql,params).fetchall()]

def params_for(meta,start=None,end=None,category='',state=''):
    start,end=start or meta['start'],end or meta['end']
    try: a,b=date.fromisoformat(start),date.fromisoformat(end)
    except ValueError: raise ValueError('Dates must be valid ISO dates (YYYY-MM-DD).')
    if a>b: raise ValueError('Start date must be on or before end date.')
    if a.year<1900 or b.year>2100: raise ValueError('Dates must fall between 1900 and 2100.')
    if (b-a).days>36525: raise ValueError('Date range cannot exceed 100 years.')
    if category and category not in meta['categories']: raise ValueError('Unknown category.')
    if state and state not in meta['states']: raise ValueError('Unknown customer state.')
    return dict(start=start,end=end,category=category,state=state,dataset_start=meta['start'])

def insight(observation,interpretation,action,limitation):
    return dict(observation=observation,interpretation=interpretation,action=action,limitation=limitation)

def dashboard(conn,params):
    meta=metadata(conn)
    result={n:query(conn,n,params) for n in ['monthly','categories','regions','frequency','delivery','reviews']}
    k=query(conn,'kpis',params)[0]
    k.update(query(conn,'repeat_customers',params)[0])
    result['kpis']=k
    start,end=date.fromisoformat(params['start']),date.fromisoformat(params['end'])
    prev_end=start-timedelta(days=1)
    prev_start=prev_end-timedelta(days=(end-start).days)
    previous={**params,'start':prev_start.isoformat(),'end':prev_end.isoformat()}
    prior=query(conn,'kpis',previous)[0]
    prior.update(query(conn,'repeat_customers',previous)[0])
    comparable=previous['start']>=meta['start'] and previous['end']<=meta['end'] and params['end']<=meta['end']
    result['comparison']={'start':previous['start'],'end':previous['end'],'complete':comparable,'values':prior,
       'changes':{key:(k[key]/prior[key]-1 if comparable and k[key] is not None and prior[key] not in [0,None] else None)
                  for key in ['sales','placed_orders','aov','repeat_rate','cancellation_rate','late_rate']}}
    cohort_params={**params,'end':min(params['end'],meta['end'])}
    result['cohorts']=query(conn,'cohorts',cohort_params)
    findings=[]
    if result['categories']:
        top=result['categories'][0]
        share=f"{top['sales_share']:.1%}" if top['sales_share'] is not None else 'an unavailable share'
        findings.append(insight(f"{top['category'].replace('_',' ').title()} contributes {share} of selected delivered merchandise sales.",
            'This is the largest category contribution in the selected scope.', 'Compare category mix and stock availability over time.',
            'Item-level sales exclude freight; category order counts overlap. No profitability data is available.'))
    groups={r['delivery_status']:r for r in result['reviews']}
    if all(g in groups and groups[g]['reviewed_orders'] for g in ['Late','On time']):
        late,ontime=groups['Late'],groups['On time']
        findings.append(insight(f"Late orders average {late['average_review']:.2f}/5 ({late['reviewed_orders']:,} reviews); on-time orders average {ontime['average_review']:.2f}/5 ({ontime['reviewed_orders']:,} reviews).",
            'Delivery experience may be associated with review scores.', 'Compare this pattern within states and categories before prioritizing investigation.',
            'This is an association, not causation; non-response and product mix may influence scores.'))
    if k['repeat_rate'] is not None:
        findings.append(insight(f"{k['repeat_customers']:,} of {k['customers']:,} purchasing customers placed at least two delivered orders ({k['repeat_rate']:.1%}).",
            'Repeat purchasing contributes to the selected customer mix.', 'Inspect complete monthly cohorts for differences in repeat activity.',
            'Repeat rate is measured within the active filters and is sensitive to the length of the date window.'))
    changes=result['comparison']['changes']
    if changes['sales'] is not None and changes['aov'] is not None and prior['eligible_delivered_orders']:
        order_change=k['eligible_delivered_orders']/prior['eligible_delivered_orders']-1
        findings.append(insight(f"Sales changed {changes['sales']:+.1%}; eligible delivered orders {order_change:+.1%}; AOV {changes['aov']:+.1%} versus the previous equal-length period.",
            'Sales changes reflect both order volume and spend per eligible order.', 'Compare product mix and seasonal patterns in each period.',
            'This arithmetic decomposition does not establish why purchasing changed.'))
    result.update(meta=meta,filters=params,findings=findings)
    return result
