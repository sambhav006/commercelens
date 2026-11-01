"""Deterministic, Olist-shaped fixture. No generated result represents Olist."""
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

FILES = {
    'orders': 'olist_orders_dataset.csv',
    'items': 'olist_order_items_dataset.csv',
    'customers': 'olist_customers_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'translations': 'product_category_name_translation.csv',
    'payments': 'olist_order_payments_dataset.csv',
    'reviews': 'olist_order_reviews_dataset.csv',
}

def generate(folder: Path, seed=42, count=4200):
    folder.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    cats = [('beleza_saude', 'health_beauty'), ('cama_mesa_banho', 'bed_bath_table'),
            ('esporte_lazer', 'sports_leisure'), ('informatica_acessorios', 'computers_accessories'),
            ('moveis_decoracao', 'furniture_decor'), ('utilidades_domesticas', 'housewares'),
            ('relogios_presentes', 'watches_gifts'), ('telefonia', 'telephony')]
    products = [dict(product_id=f'p{i:04}', product_category_name=cats[i % 8][0] if i % 47 else None,
                     product_weight_g=100+i*7) for i in range(160)]
    rows = {k: [] for k in FILES}
    rows['products'] = products
    rows['translations'] = [dict(product_category_name=a, product_category_name_english=b) for a,b in cats]
    identities = []
    for i in range(count):
        oid, cid = f'o{i:06}', f'c{i:06}'
        # Rising order volume, seasonality and repeat identities across customer_id values.
        offset = int((rng.random() ** .81) * 730)
        purchase = datetime(2023,1,1) + timedelta(days=offset, hours=rng.randrange(24))
        if i == 0: purchase = datetime(2023,1,1)
        if i == count-1: purchase = datetime(2024,12,31,12)
        if identities and rng.random() < .24:
            uid, state = rng.choice(identities)
        else:
            uid = f'u{i:06}'
            state = rng.choices(['SP','RJ','MG','RS','PR','BA','PE','AM'], [35,17,14,9,9,7,6,3])[0]
            identities.append((uid,state))
        status = rng.choices(['delivered','canceled','shipped','unavailable'],[90,5,4,1])[0]
        estimate = purchase + timedelta(days=rng.randint(12,24))
        late = rng.random() < (.34 if state in ['AM','BA','PE'] else .13)
        arrival = estimate + timedelta(days=rng.randint(1,13) if late else -rng.randint(0,9))
        actual = arrival.strftime('%Y-%m-%d %H:%M:%S') if status == 'delivered' and i % 71 else None
        rows['orders'].append(dict(order_id=oid,customer_id=cid,order_status=status,
            order_purchase_timestamp=purchase.strftime('%Y-%m-%d %H:%M:%S'),
            order_delivered_customer_date=actual,
            order_estimated_delivery_date=estimate.strftime('%Y-%m-%d %H:%M:%S') if i % 113 else None))
        rows['customers'].append(dict(customer_id=cid,customer_unique_id=uid,customer_state=state,
                                      customer_city=state.lower(),customer_zip_code_prefix='00000'))
        total = 0
        for j in range(rng.choices([1,2,3,4],[66,25,7,2])[0]):
            p = rng.randrange(160)
            price = round(rng.lognormvariate(4.4 + (p % 8)*.075, .55)*(1+offset/730*.12),2)
            freight = round(rng.uniform(8,36),2)
            total += price + freight
            rows['items'].append(dict(order_id=oid,order_item_id=j+1,product_id=f'p{p:04}',
                                      seller_id=f's{p%20}',price=price,freight_value=freight))
        split = 2 if i % 8 == 0 else 1
        for j in range(split):
            rows['payments'].append(dict(order_id=oid,payment_sequential=j+1,payment_type='credit_card' if j==0 else 'voucher',
                                          payment_installments=rng.randint(1,6),payment_value=round(total/split,2)))
        if status == 'delivered' and rng.random() < .86:
            for j in range(2 if i % 29 == 0 else 1):
                rows['reviews'].append(dict(review_id=f'r{i:06}_{j}',order_id=oid,
                    review_score=rng.choices([1,2,3,4,5],[20,20,28,20,12] if late else [3,4,10,26,57])[0],
                    review_creation_date=(arrival+timedelta(days=1)).isoformat(' '),
                    review_answer_timestamp=(arrival+timedelta(days=j+2)).isoformat(' ')))
    # Intentional exact duplicates are documented and removed by natural key.
    rows['items'].append(rows['items'][10].copy())
    rows['customers'].append(rows['customers'][10].copy())
    for name, values in rows.items():
        pd.DataFrame(values).to_csv(folder / FILES[name], index=False, lineterminator='\n')
    return folder
