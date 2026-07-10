import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.abspath('.'))
from services.developer_audit_service import DeveloperAuditService
p=tempfile.mkdtemp()
db=os.path.join(p,'x.db')
audit=DeveloperAuditService(db)
audit.log_company_audit('tester','admin_company','company_name','Old','New')
with sqlite3.connect(db) as conn:
    rows=conn.execute('SELECT id,field_name,old_value,new_value,source FROM company_profile_audit').fetchall()
    print('direct audit rows:', rows)
