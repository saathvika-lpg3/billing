from pathlib import Path
import sqlite3
import sys
import re
from datetime import datetime

# ensure project root is on sys.path so top-level `services` package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.pdf_print import write_transaction_pdf

DB = Path('database/prm_billing_inventory.db')
OUT = Path('prints/sample_invoice.pdf')
OUT.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row
    company = dict(conn.execute('SELECT * FROM company LIMIT 1').fetchone())

header = {
    'bill_no': 'SAMPLE-001',
    'bill_date': datetime.now().date().isoformat(),
    'customer_name': 'Demo Customer',
    'billing_address': 'Demo Address, City',
}

lines = []
rates = [5, 12, 18, 0, 18, 12]
for i, rate in enumerate(rates, start=1):
    qty = 1 + i
    taxable = round(100.0 * i + 50, 2)
    gst_amt = round(taxable * rate / 100, 2)
    cgst = round(gst_amt / 2, 2) if rate and rate != 0 else 0.0
    sgst = round(gst_amt - cgst, 2) if rate and rate != 0 else 0.0
    igst = 0.0
    amount = round(taxable + gst_amt, 2)
    lines.append({
        'item': f'Demo Item {i}',
        'hsn': '9999',
        'qty': qty,
        'unit': 'pcs',
        'mrp': taxable + 10,
        'rate': taxable,
        'free': 0,
        'disc': 0,
        'taxable': taxable,
        'gst': rate,
        'cgst': cgst,
        'sgst': sgst,
        'igst': igst,
        'amount': amount,
    })

# totals
totals = {'taxable': 0.0, 'discount': 0.0, 'cgst': 0.0, 'sgst': 0.0, 'igst': 0.0, 'gst_total': 0.0}
for r in lines:
    totals['taxable'] += float(r['taxable'])
    totals['cgst'] += float(r.get('cgst') or 0)
    totals['sgst'] += float(r.get('sgst') or 0)
    totals['igst'] += float(r.get('igst') or 0)
    gst = float(r.get('cgst') or 0) + float(r.get('sgst') or 0) + float(r.get('igst') or 0)
    totals['gst_total'] += gst

gross = totals['taxable'] + totals['gst_total']
rounded = round(gross)
totals['round_off'] = round(rounded - gross, 2)
totals['grand_total'] = rounded

write_transaction_pdf(OUT, 'Sample Invoice', company, header, lines, totals, document_type='sales_invoice')
data = OUT.read_bytes()
pages = len(re.findall(rb"/Type\s*/Page\b", data))
print('WROTE', OUT, 'PAGES', pages)
