from pathlib import Path
import ast
import json
import re
from typing import Any

old_root = Path('D:/PRM_BILLING_INVENTORY/src/prm_billing_inventory')
new_root = Path('D:/PRM_GST_DESKTOP')


def parse_ast_assignments(path: Path, target_name: str) -> Any:
    text = path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    return ast.literal_eval(node.value)
    return None


def extract_old_top_menu():
    return parse_ast_assignments(old_root / 'app.py', 'ERP_TOP_MENU') or []


def extract_old_module_defs():
    path = old_root / 'module_catalog.py'
    if not path.exists():
        return []
    text = path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(text)
    modules = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'MODULE_GROUPS':
                    modules = ast.literal_eval(node.value)
                    return modules
    return []


def extract_current_operations():
    path = new_root / 'views' / 'module_hub_view.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(text)
    operations = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id.endswith('_OPERATIONS'):
            value = node.value
            if isinstance(value, ast.List):
                for elt in value.elts:
                    if isinstance(elt, ast.Call) and isinstance(elt.func, ast.Name) and elt.func.id == 'ModuleOperation':
                        args = [ast.literal_eval(arg) for arg in elt.args]
                        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in elt.keywords}
                        operations.append({'group': node.targets[0].id, 'args': args, 'kwargs': kwargs})
    return operations


def extract_document_catalog():
    return parse_ast_assignments(new_root / 'views' / 'document_center_view.py', 'DOCUMENT_CATALOG') or []


def extract_print_doc_meta():
    return parse_ast_assignments(new_root / 'views' / 'document_center_view.py', 'PRINT_DOC_META') or {}


def extract_current_business_types():
    path = new_root / 'services' / 'company_profile_service.py'
    types = []
    text = path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'business_types':
            # find return list literal
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.List):
                    for elt in sub.value.elts:
                        if isinstance(elt, ast.Dict):
                            d = {ast.literal_eval(k): ast.literal_eval(v) for k,v in zip(elt.keys, elt.values)}
                            types.append(d)
                    return types
    return types


def extract_business_profiles():
    path = new_root / 'services' / 'business_rules.py'
    text = path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(text)
    profiles = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'BUSINESS_PROFILES':
                    value = node.value
                    if isinstance(value, ast.Dict):
                        for key_node, val_node in zip(value.keys, value.values):
                            code = ast.literal_eval(key_node)
                            if isinstance(val_node, ast.Call) and isinstance(val_node.func, ast.Name) and val_node.func.id == 'BusinessProfile':
                                profile = {}
                                for kw in val_node.keywords:
                                    profile[kw.arg] = ast.literal_eval(kw.value)
                                profiles[code] = profile
                    return profiles
    return profiles


def extract_feature_matrix():
    path = new_root / 'AI_GUIDE' / '08_ERP_FEATURE_MATRIX.md'
    if not path.exists():
        return []
    text = path.read_text(encoding='utf-8', errors='ignore')
    matrix = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    start = None
    headers = []
    for i, line in enumerate(lines):
        if line.startswith('|') and 'Business type' in line:
            headers = [h.strip() for h in line.split('|')[1:-1]]
            start = i+2
            break
    if start is None:
        return []
    for line in lines[start:]:
        if not line.startswith('|'): break
        cols = [c.strip() for c in line.split('|')[1:-1]]
        if len(cols) == len(headers):
            matrix.append(dict(zip(headers, cols)))
        else:
            break
    return matrix


def normalize_key(key: str) -> str:
    if key.startswith('module:') or key.startswith('new:'):
        return key.split(':', 1)[1]
    return key


def main():
    old_menu = extract_old_top_menu()
    old_modules = extract_old_module_defs()
    current_ops = extract_current_operations()
    document_catalog = extract_document_catalog()
    print_meta = extract_print_doc_meta()
    current_types = extract_current_business_types()
    profiles = extract_business_profiles()
    matrix = extract_feature_matrix()

    old_menu_keys = set(normalize_key(item[1]) for group, items in old_menu for item in items)
    current_keys = set(op['args'][1] for op in current_ops if len(op['args']) > 1)
    overlap = old_menu_keys & current_keys
    old_only = sorted(old_menu_keys - current_keys)
    current_only = sorted(current_keys - old_menu_keys)

    summary = {
        'old_menu_group_count': len(old_menu),
        'old_module_count': len(old_modules),
        'current_operation_count': len(current_ops),
        'document_catalog': document_catalog,
        'print_doc_meta': list(print_meta.keys()),
        'current_business_types': current_types,
        'business_profiles': profiles,
        'feature_matrix': matrix,
        'old_only_keys': old_only,
        'current_only_keys': current_only,
        'common_keys': sorted(overlap),
    }
    out = Path('.business_type_report.json')
    out.write_text(json.dumps(summary, indent=2), encoding='utf-16')
    print('written', out)


if __name__ == '__main__':
    main()
