from pathlib import Path
import json

p = Path('D:/PRM_GST_DESKTOP/.business_type_parity_analysis_output.json')
text = p.read_text(encoding='utf-16')
try:
    data = json.loads(text)
except Exception as exc:
    print('JSON_ERR', exc)
    raise
print('keys', list(data.keys()))
print('old_menu_groups', len(data['old_menu_groups']))
print('old_module_defs', len(data['old_module_defs']))
print('current_operations', len(data['current_operations']))
print('company_business_types', data['company_business_types'])
print('business_profiles', sorted(data['business_profiles'].keys()))
for code, profile in data['business_profiles'].items():
    print('PROFILE', code)
    print('  name', profile['name'])
    print('  required_fields', profile['required_fields'])
    print('  columns', profile['columns'])
    print('  print_template_type', profile['print_template_type'])
    print('  validation', profile['validation'])
