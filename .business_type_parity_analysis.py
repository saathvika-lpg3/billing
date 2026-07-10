from pathlib import Path
import ast
import re
import json

old_root = Path('D:/PRM_BILLING_INVENTORY/src/prm_billing_inventory')
new_root = Path('D:/PRM_GST_DESKTOP')


def extract_old_erp_menu():
    p = old_root / 'app.py'
    text = p.read_text(encoding='utf-8', errors='ignore')
    idx = text.find('ERP_TOP_MENU')
    if idx == -1:
        return []
    sub = text[idx:]
    start = sub.find('(')
    level = 0
    end = None
    for i, ch in enumerate(sub[start:], start):
        if ch == '(':
            level += 1
        elif ch == ')':
            level -= 1
            if level == 0:
                end = i + 1
                break
    if end is None:
        return []
    menu_text = sub[start:end]
    return ast.literal_eval(menu_text)


def extract_old_module_catalog():
    p = old_root / 'module_catalog.py'
    text = p.read_text(encoding='utf-8', errors='ignore')
    modules = []
    # simplistic parse for module(...) calls
    for m in re.finditer(r'module\(([^\)]*)\)', text, flags=re.S):
        args = [a.strip() for a in m.group(1).split(',')]
        cleaned = []
        for a in args:
            a = a.strip()
            if a.startswith(('"', "'")) and a.endswith(('"', "'")):
                cleaned.append(ast.literal_eval(a))
            else:
                cleaned.append(a)
        modules.append(cleaned)
    return modules


def extract_current_operations():
    path = new_root / 'views' / 'module_hub_view.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    ops = []
    for m in re.finditer(r'ModuleOperation\(([^\)]*)\)', text, flags=re.S):
        raw = m.group(1)
        items = []
        depth = 0
        current = ''
        for ch in raw:
            if ch == ',' and depth == 0:
                items.append(current.strip())
                current = ''
                continue
            current += ch
            if ch in '([{' :
                depth += 1
            elif ch in ')]}':
                depth -= 1
        if current:
            items.append(current.strip())
        args = []
        for item in items:
            if item.startswith(('"', "'")) and item.endswith(('"', "'")):
                args.append(ast.literal_eval(item))
            else:
                args.append(item)
        ops.append(args)
    return ops


def extract_doc_catalog():
    path = new_root / 'views' / 'document_center_view.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    docs = []
    m = re.search(r'DOCUMENT_CATALOG\s*=\s*\[', text)
    if m:
        sub = text[m.end()-1:]
        level = 0
        end = None
        for i, ch in enumerate(sub):
            if ch == '[':
                level += 1
            elif ch == ']':
                level -= 1
                if level == 0:
                    end = i + 1
                    break
        if end:
            docs = ast.literal_eval(sub[:end])
    return docs


def extract_print_doc_meta():
    path = new_root / 'views' / 'document_center_view.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    metas = {}
    m = re.search(r'PRINT_DOC_META\s*=\s*\{', text)
    if m:
        sub = text[m.end()-1:]
        level = 0
        end = None
        for i, ch in enumerate(sub):
            if ch == '{':
                level += 1
            elif ch == '}':
                level -= 1
                if level == 0:
                    end = i+1
                    break
        if end:
            metas = ast.literal_eval(sub[:end])
    return metas


def extract_business_profiles():
    path = new_root / 'services' / 'business_rules.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    profiles = {}
    m = re.search(r'BUSINESS_PROFILES\s*:\s*dict\[str, BusinessProfile\] = \{', text)
    if m:
        sub = text[m.end()-1:]
        level = 0
        end = None
        for i, ch in enumerate(sub):
            if ch == '{':
                level += 1
            elif ch == '}':
                level -= 1
                if level == 0:
                    end = i+1
                    break
        if end:
            body = sub[:end]
            # not easy to literal eval because of field names; use regex to capture code and name pairs
            for m2 in re.finditer(r'"([^"]+)"\s*:\s*BusinessProfile\(([^\)]*)\)', body, flags=re.S):
                code = m2.group(1)
                args = m2.group(2)
                name = re.search(r'name\s*=\s*"([^"]+)"', args)
                required_fields = re.search(r'required_fields\s*=\s*\(([^\)]*)\)', args)
                columns = re.search(r'columns\s*=\s*\(([^\)]*)\)', args)
                print_template = re.search(r'print_template_type\s*=\s*"([^"]+)"', args)
                validation = re.search(r'validation_rules\s*=\s*\{([^\}]*)\}', args, flags=re.S)
                profiles[code] = {
                    'name': name.group(1) if name else '',
                    'required_fields': [f.strip().strip('"\'') for f in required_fields.group(1).split(',') if f.strip()] if required_fields else [],
                    'columns': [f.strip().strip('"\'') for f in columns.group(1).split(',') if f.strip()] if columns else [],
                    'print_template_type': print_template.group(1) if print_template else '',
                    'validation': [k.strip().split(':')[0].strip(' "\'') for k in validation.group(1).split(',') if k.strip()] if validation else [],
                }
    return profiles


def extract_company_business_types():
    path = new_root / 'services' / 'company_profile_service.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    result = []
    m = re.search(r'return \[([^\]]*)\]', text, flags=re.S)
    if m:
        body = m.group(1)
        for m2 in re.finditer(r'\{([^\}]*)\}', body, flags=re.S):
            d = m2.group(1)
            code = re.search(r'"code"\s*:\s*"([^"]+)"', d)
            name = re.search(r'"name"\s*:\s*"([^"]+)"', d)
            invoice = re.search(r'"invoice_template_code"\s*:\s*"([^"]+)"', d)
            if code and name:
                result.append({'code': code.group(1), 'name': name.group(1), 'invoice_template_code': invoice.group(1) if invoice else ''})
    return result


def extract_erp_feature_matrix():
    path = new_root / 'AI_GUIDE' / '08_ERP_FEATURE_MATRIX.md'
    text = path.read_text(encoding='utf-8', errors='ignore')
    matrix = []
    in_table = False
    headers = []
    for line in text.splitlines():
        if line.startswith('|') and 'Business type' in line:
            in_table = True
            headers = [h.strip() for h in line.split('|')[1:-1]]
            continue
        if in_table and line.startswith('|'):
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if len(cols) == len(headers):
                matrix.append(dict(zip(headers, cols)))
            else:
                # maybe end of table
                if line.strip() == '':
                    break
    return matrix


def extract_dev_console_business_types():
    path = new_root / 'views' / 'developer_console_view.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    types = []
    m = re.search(r'widget\.addItems\(business_labels or \[([^\]]*)\]\)', text)
    if m:
        return []
    return types

old_menu = extract_old_erp_menu()
old_modules = extract_old_module_catalog()
current_ops = extract_current_operations()
doc_catalog = extract_doc_catalog()
print_meta = extract_print_doc_meta()
business_profiles = extract_business_profiles()
company_types = extract_company_business_types()
feature_matrix = extract_erp_feature_matrix()

output = {
    'old_menu_groups': [(grp, [(item[0], item[1]) for item in items]) for grp, items in old_menu],
    'old_module_defs': old_modules,
    'current_operations': current_ops,
    'document_catalog': doc_catalog,
    'print_doc_meta_keys': list(print_meta.keys()),
    'business_profiles': business_profiles,
    'company_business_types': company_types,
    'feature_matrix': feature_matrix,
}
print(json.dumps(output, indent=2))
