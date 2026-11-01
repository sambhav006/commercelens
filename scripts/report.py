"""Rebuild factual portfolio report and human-readable metric dictionary from local data."""
import json
import re
from contextlib import closing
from backend.analytics import connect, metadata, params_for, dashboard
from backend.pipeline import ROOT

def main():
    with closing(connect()) as c:
        m=metadata(c)
        d=dashboard(c,params_for(m))
        # Matched calendar years have different day counts; use the exact prior-period engine.
        growth=dashboard(c,params_for(m,start='2024-01-02',end='2024-12-31')) if m['mode']=='synthetic' else None
    k=d['kpis']
    def n(value,digits=0): return 'Unavailable' if value is None else f'{value:,.{digits}f}'
    def p(value):return 'Unavailable' if value is None else f'{value:.1%}'
    text=[f"# CommerceLens analysis report\n\n**Source: {m['source']}.**",
          'These results describe generated fixtures, not a real business. Do not claim commercial impact.' if m['mode']=='synthetic' else 'Descriptive findings from locally supplied Olist files; no causal or profit claims.',
          f"Purchase window: **{m['start']} to {m['end']}**. Ingested: {m['ingested_at']}. All categories and customer states.\n",
          '| KPI | Result |\n|---|---:|',
          f"| Delivered merchandise sales (BRL, excluding freight) | {n(k['sales'],2)} |",
          f"| Eligible delivered orders | {n(k['eligible_delivered_orders'])} |",
          f"| Total placed orders | {n(k['placed_orders'])} |",
          f"| Delivered-order AOV (BRL) | {n(k['aov'],2)} |",
          f"| Repeat customers / purchasing customers | {n(k['repeat_customers'])} / {n(k['customers'])} ({p(k['repeat_rate'])}) |",
          f"| Canceled / placed orders | {n(k['canceled_orders'])} / {n(k['placed_orders'])} ({p(k['cancellation_rate'])}) |",
          f"| Late / valid-date delivered orders | {n(k['late_orders'])} / {n(k['delivery_sample'])} ({p(k['late_rate'])}) |",
          '\n## Findings\n']
    findings=list(d['findings'])
    if growth:
        findings += [f for f in growth['findings'] if f['observation'].startswith('Sales changed')]
        text.append(f"Growth comparison uses 2024-01-02 to 2024-12-31 versus {growth['comparison']['start']} to {growth['comparison']['end']}: two immediately adjacent 365-day windows.\n")
    for i,f in enumerate(findings,1):
        text += [f"### {i}. Observation\n\n{f['observation']}",f"**Possible interpretation:** {f['interpretation']}",
                 f"**Proposed investigation:** {f['action']}",f"**Limitation:** {f['limitation']}\n"]
    text += ['## Regional context\n','| Customer state | Sales (BRL) | Late rate | Valid-date orders |\n|---|---:|---:|---:|']
    for r in d['regions']:text.append(f"| {r['state']} | {n(r['sales'],2)} | {p(r['late_rate'])} | {n(r['delivery_sample'])} |")
    text += ['\n## Scope and limitations\n',
       'All patterns in demo mode are consequences of the generator. The generator intentionally varies delay probabilities and review scores; it cannot support real operational recommendations.',
       'First purchase means first observed delivered purchase. Cohort month zero is the acquisition baseline; future or incomplete months are unavailable. Repeat rate measures repeat orders within the selected period.',
       'Review non-response, product mix and geography can confound associations. Delivery missingness changes the denominator. Current order statuses may bias recent purchase periods.',
       'Sales exclude freight and entire orders with incomplete prices. No costs, profit, margins, returns, discounts or channels are inferred.',
       'Rebuild this report after changing the source: `python -m scripts.report`. Dashboard and exports always use the current database; this document is a dated snapshot.']
    report=re.sub(r'(?m)(^\|[^\n]*)\n\n(?=\|)',r'\1\n','\n\n'.join(text))
    (ROOT/'docs/analysis-report.md').write_text(report,encoding='utf-8')
    metrics=json.loads((ROOT/'docs/metrics.json').read_text())
    dictionary=['# Metric dictionary','Generated from `docs/metrics.json`, also served by `/api/methodology`. NULL values display as Unavailable. Counts can validly be zero.']
    for metric in metrics:
        dictionary.append('## '+metric['name'])
        dictionary.extend(f"- **{key.title()}:** {value}" for key,value in metric.items() if key!='name')
    (ROOT/'docs/metric-dictionary.md').write_text('\n\n'.join(dictionary)+'\n',encoding='utf-8')
    print('Updated docs/analysis-report.md and docs/metric-dictionary.md')

if __name__=='__main__':main()
