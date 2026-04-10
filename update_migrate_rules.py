import re

with open('migrate_rules.py', 'r') as f:
    code = f.read()

# Add hardbones logic
HARDBONES = ["corp.kuaishou.com", "kuaishou.com", "streamlake.com", "streamlake.ai"]

clash_hardbone_rules = "".join([f"  - DOMAIN-SUFFIX,{hb},DIRECT\n" for hb in HARDBONES])
surfboard_hardbone_rules = "".join([f"DOMAIN-SUFFIX,{hb},DIRECT\n" for hb in HARDBONES])

# Modify process_clash
# We need to insert rules to new_lines right after new_lines = lines[:rules_start+1]
code = code.replace(
    "new_lines = lines[:rules_start+1]",
    f"new_lines = lines[:rules_start+1]\n    new_lines.append('\\n  # 硬骨头强制直连区\\n')\n    for hb in {HARDBONES}:\n        new_lines.append(f'  - DOMAIN-SUFFIX,{{hb}},DIRECT\\n')"
)

# And inject array into fake-ip-filter if it exists
clash_fakeip_inject = f"""    
    inject_idx = -1
    for idx, l in enumerate(new_lines):
        if l.strip() == 'fake-ip-filter:':
            inject_idx = idx
            break
    if inject_idx != -1:
        for hb in {HARDBONES}:
            new_lines.insert(inject_idx + 1, f"    - \\"*.{{hb}}\\"\\n")
            new_lines.insert(inject_idx + 1, f"    - \\"{{hb}}\\"\\n")
"""
code = code.replace(
    "with open(file_path, 'w', encoding='utf-8') as f:\n        f.writelines(new_lines)",
    clash_fakeip_inject + "\n    with open(file_path, 'w', encoding='utf-8') as f:\n        f.writelines(new_lines)"
)

# Modify process_surfboard
code = code.replace(
    "new_lines = lines[:rules_start+1]",
    f"new_lines = []\n    for l in lines[:rules_start+1]:\n        if l.startswith('skip-proxy ='):\n            append_list = ', '.join([f'*.{{d}}, {{d}}' for d in {HARDBONES}])\n            l = l.strip() + ', ' + append_list + '\\n'\n        new_lines.append(l)\n    \n    new_lines.append('\\n# 硬骨头强制直连区\\n')\n    for hb in {HARDBONES}:\n        new_lines.append(f'DOMAIN-SUFFIX,{{hb}},DIRECT\\n')"
)

# Modify process_shadowrocket
code = code.replace(
    "new_lines = lines[:rules_start+1]",
    f"new_lines = []\n    for l in lines[:rules_start+1]:\n        if l.startswith('skip-proxy ='):\n            append_list = ', '.join([f'*.{{d}}, {{d}}' for d in {HARDBONES}])\n            l = l.strip() + ', ' + append_list + '\\n'\n        new_lines.append(l)\n    \n    new_lines.append('\\n# 硬骨头强制直连区\\n')\n    for hb in {HARDBONES}:\n        new_lines.append(f'DOMAIN-SUFFIX,{{hb}},DIRECT\\n')"
)

# Modify process_singbox
singbox_inject = f"""
    # Hardbone routing logic
    has_local = any(s.get('tag') == 'local' for s in data['dns']['servers'])
    if not has_local:
        data['dns']['servers'].append({{"tag": "local", "address": "local", "detour": "direct"}})
        
    dns_rules = data.get('dns', {{}}).get('rules', [])
    dns_rules.insert(0, {{
        "domain_suffix": {HARDBONES},
        "server": "local"
    }})
    data['dns']['rules'] = dns_rules

    new_rules.insert(0, {{
        "outbound": "direct",
        "domain_suffix": {HARDBONES}
    }})
"""
code = code.replace(
    "new_rules = dns_rules.copy()",
    "new_rules = dns_rules.copy()\n" + singbox_inject
)

with open('migrate_rules_new.py', 'w') as f:
    f.write(code)

