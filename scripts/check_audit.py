import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.company_profile_service import CompanyProfileService
import sqlite3, tempfile
p=tempfile.mkdtemp()
db=os.path.join(p,'x.db')
service=CompanyProfileService(db)
service.ensure_schema()
print('schema created at', db)
service.save_profile({'company_name':'ACME','phone':'111'}, developer=False)
print('first save done')
service.save_profile({'company_name':'ACME Co','phone':'222'}, developer=False)
print('second save done')
with sqlite3.connect(db) as conn:
    cur = conn.execute('SELECT id,changed_at,changed_by,source,field_name,old_value,new_value FROM company_profile_audit')
    rows = cur.fetchall()
    print('audit rows:', rows)
    print('company columns:', conn.execute("PRAGMA table_info(company)").fetchall())
    print('audit columns:', conn.execute("PRAGMA table_info(company_profile_audit)").fetchall())
    print('company row:', conn.execute('SELECT * FROM company').fetchall())
