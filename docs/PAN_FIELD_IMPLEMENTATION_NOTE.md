# PAN Field Implementation Note

## Summary
Added PAN support to the developer dashboard company-management flow so a PAN number can be entered, saved, and loaded alongside the existing company profile fields.

## What changed
- Added a PAN field to the Developer Console company profile form.
- Extended the company profile persistence layer to store PAN in the company and dev_companies records.
- Added PAN to the shared Company Settings master screen so it is available in the general company settings flow.
- Added a regression test covering PAN persistence through the company profile service.

## Files updated
- views/developer_console_view.py
- services/company_profile_service.py
- services/sqlite_source.py
- services/master_repository.py
- views/simple_master_view.py
- tests/test_company_profile_service.py

## Verification
Verified with:
- python -c "import sqlite3, tempfile; from pathlib import Path; from services.company_profile_service import CompanyProfileService; tmpdir = tempfile.mkdtemp(); db_path = Path(tmpdir) / 'company_profile_test.db'; service = CompanyProfileService(db_path); service.save_profile({'company_name':'Acme Trading','pan':'ABCDE1234F'}, developer=True); profile = service.current_profile(); print('PROFILE_PAN', profile.get('pan')); conn = sqlite3.connect(db_path); print('DB_PAN', conn.execute('SELECT pan FROM company LIMIT 1').fetchone()[0]); conn.close()"

Output:
- PROFILE_PAN ABCDE1234F
- DB_PAN ABCDE1234F
