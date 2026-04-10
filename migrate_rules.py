import os
import json

md_path = "/Users/pengli/Desktop/Clash 分流升级/分流规则参考.md"
v2b_dir = "/Users/pengli/Desktop/Clash 分流升级/v2b"

HARDBONES = [
    "corp.kuaishou.com", "kuaishou.com", "streamlake.com", "streamlake.ai",
    "todesk.com", "oray.com", "oray.cn", "sunlogin.net", "sunlogin.com",
    "cmbchina.com", "cmbchina.cn", "pingan.com", "pingan.com.cn", "spdb.com.cn",
    "alipayhk.com", "alipay.hk", "hsbc.com.hk", "hsbc.com", "bochk.com", "za.group", "antbank.hk",
    "futunn.com", "futu5.com", "futuhk.com"
]

def parse_md_rules(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_lines = f.readlines()
        
    rules_start = -1
    for i, line in enumerate(md_lines):
        if line.strip() == 'rules:':
            rules_start = i
            break
            
    if rules_start == -1:
        print("Cannot find 'rules:' in the MD file")
        return []
        
    md_rules_raw = md_lines[rules_start+1:]
    
    parsed_rules = []
    for line in md_rules_raw:
        line = line.strip()
        if not line or not line.startswith('- '):
            continue
            
        parts = line[2:].split(',')
        rule_type = parts[0].strip()
        
        policy_idx = 1 if rule_type.upper() == 'MATCH' else 2
        
        if len(parts) > policy_idx:
            raw_policy = parts[policy_idx].strip()
            
            if raw_policy == '🎯 全球直连':
                policy = 'DIRECT'
            elif raw_policy == '🛑 全球拦截':
                policy = 'REJECT'
            else:
                policy = 'PROXY'
                
            payload = parts[1].strip() if policy_idx > 1 else ""
            options = [p.strip() for p in parts[policy_idx+1:]] if len(parts) > policy_idx + 1 else []
            
            parsed_rules.append({
                "type": rule_type,
                "payload": payload,
                "policy": policy,
                "options": options
            })
            
    return parsed_rules

def process_clash(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    rules_start = -1
    for i, line in enumerate(lines):
        if line.strip() == 'rules:':
            rules_start = i
            break
            
    if rules_start == -1:
        print(f"Skipping {os.path.basename(file_path)}: Cannot find 'rules:'")
        return
        
    new_lines = []
    # Copy until rules:
    for l in lines[:rules_start+1]:
        # Filter out previous hardbone injections so we don't duplicate
        skip = False
        for hb in HARDBONES:
            if l.strip() == f'- "*.{hb}"' or l.strip() == f'- "{hb}"':
                skip = True
            if l.strip() == f'"+.{hb}": "system"' or l.strip() == f'"{hb}": "system"':
                skip = True
            if l.strip() == f'"+.{hb}": "dhcp://system"' or l.strip() == f'"{hb}": "dhcp://system"':
                skip = True
        if skip: continue
        
        new_lines.append(l)
        if l.strip() == 'fake-ip-filter:':
            for hb in HARDBONES:
                new_lines.append(f"    - \"*.{hb}\"\n")
                new_lines.append(f"    - \"{hb}\"\n")
                
    # Inject nameserver-policy for hardbones to dhcp://system
    ns_idx = -1
    for idx, l in enumerate(new_lines):
        if l.strip() == 'nameserver-policy:':
            ns_idx = idx
            break
    if ns_idx != -1:
        for hb in HARDBONES:
            new_lines.insert(ns_idx + 1, f"    \"+.{hb}\": \"dhcp://system\"\n")
            new_lines.insert(ns_idx + 1, f"    \"{hb}\": \"dhcp://system\"\n")
    else:
        dns_idx = -1
        for idx, l in enumerate(new_lines):
            if l.strip() == 'dns:':
                dns_idx = idx
                break
        if dns_idx != -1:
            new_lines.insert(dns_idx + 1, "  nameserver-policy:\n")
            for hb in HARDBONES:
                new_lines.insert(dns_idx + 2, f"    \"+.{hb}\": \"dhcp://system\"\n")
                new_lines.insert(dns_idx + 2, f"    \"{hb}\": \"dhcp://system\"\n")

    new_lines.append('\n  # 硬骨头内网放行区 (Highest Priority)\n')
    for hb in HARDBONES:
        new_lines.append(f'  - DOMAIN-SUFFIX,{hb},DIRECT\n')
        
    new_lines.append('\n  # 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        new_lines.append(f'  - IP-CIDR,{cidr},DIRECT\n')
    for cidr6 in ["::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]:
        new_lines.append(f'  - IP-CIDR6,{cidr6},DIRECT\n')
        
    for r in rules:
        policy = '$app_name' if r['policy'] == 'PROXY' else r['policy']
        if r['type'].upper() == 'MATCH':
            new_lines.append(f"  - MATCH,{policy}\n")
        else:
            opt_str = f",{','.join(r['options'])}" if r['options'] else ""
            new_lines.append(f"  - {r['type']},{r['payload']},{policy}{opt_str}\n")
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully migrated Clash format: {os.path.basename(file_path)}")

def process_surfboard(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    rules_start = -1
    for i, line in enumerate(lines):
        if line.strip() == '[Rule]':
            rules_start = i
            break
            
    if rules_start == -1:
        print(f"Skipping {os.path.basename(file_path)}: Cannot find '[Rule]'")
        return
        
    new_lines = []
    # Inject into skip-proxy
    for l in lines[:rules_start+1]:
        if l.startswith('skip-proxy ='):
            missing = [d for d in HARDBONES if d not in l]
            if missing:
                append_list = ', '.join([f'*.{d}, {d}' for d in missing])
                l = l.strip() + ', ' + append_list + '\n'
        new_lines.append(l)
    
    new_lines.append('\n# 硬骨头内网放行区 (Highest Priority)\n')
    for hb in HARDBONES:
        new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\n')
        
    new_lines.append('\n# 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        new_lines.append(f'IP-CIDR,{cidr},DIRECT,no-resolve\n')
    for cidr6 in ["::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]:
        new_lines.append(f'IP-CIDR6,{cidr6},DIRECT,no-resolve\n')
        
    for r in rules:
        policy = '$app_name' if r['policy'] == 'PROXY' else r['policy']
        if r['type'].upper() == 'MATCH':
            new_lines.append(f"FINAL,{policy}\n")
        else:
            opt_str = f",{','.join(r['options'])}" if r['options'] else ""
            new_lines.append(f"{r['type']},{r['payload']},{policy}{opt_str}\n")
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully migrated Surfboard format: {os.path.basename(file_path)}")

def process_shadowrocket(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    rules_start = -1
    rules_end = -1
    for i, line in enumerate(lines):
        if line.strip() == '[Rule]':
            rules_start = i
        elif rules_start != -1 and line.strip().startswith('[') and line.strip().endswith(']'):
            rules_end = i
            break
            
    if rules_start == -1:
        print(f"Skipping {os.path.basename(file_path)}: Cannot find '[Rule]'")
        return
        
    if rules_end == -1:
        rules_end = len(lines)
        
    new_lines = []
    for l in lines[:rules_start+1]:
        if l.startswith('skip-proxy ='):
            missing = [d for d in HARDBONES if d not in l]
            if missing:
                append_list = ', '.join([f'*.{d}, {d}' for d in missing])
                l = l.strip() + ', ' + append_list + '\n'
        new_lines.append(l)
    
    new_lines.append('\n# 硬骨头内网放行区 (Highest Priority)\n')
    for hb in HARDBONES:
        new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\n')
        
    new_lines.append('\n# 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        new_lines.append(f'IP-CIDR,{cidr},DIRECT,no-resolve\n')
    for cidr6 in ["::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]:
        new_lines.append(f'IP-CIDR6,{cidr6},DIRECT,no-resolve\n')
    
    for r in rules:
        policy = 'PROXY' if r['policy'] == 'PROXY' else r['policy']
        if r['type'].upper() == 'MATCH':
            new_lines.append(f"FINAL,{policy}\n")
        elif r['type'].upper() == 'IP-CIDR6':
            opt_str = f",{','.join(r['options'])}" if r['options'] else ""
            new_lines.append(f"{r['type']},{r['payload']},{policy}{opt_str}\n")
        else:
            opt_str = f",{','.join(r['options'])}" if r['options'] else ""
            new_lines.append(f"{r['type']},{r['payload']},{policy}{opt_str}\n")
            
    new_lines.append("\n")
    new_lines.extend(lines[rules_end:])
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully migrated Shadowrocket format: {os.path.basename(file_path)}")

def process_singbox(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Skipping {os.path.basename(file_path)}: Not a valid JSON ({e})")
            return
            
    if 'route' not in data:
        data['route'] = {}
        
    existing_rules = data['route'].get('rules', [])
    dns_rules_orig = [x for x in existing_rules if x.get('protocol') == 'dns']
    
    new_rules = dns_rules_orig.copy()

    if 'dns' not in data:
        data['dns'] = {"servers": [], "rules": []}
    
    has_local = any(s.get('tag') == 'local' for s in data['dns'].get('servers', []))
    if not has_local:
        data['dns'].setdefault('servers', []).append({"tag": "local", "address": "local", "detour": "direct"})
        
    # Remove existing hardbone rule if present to avoid duplication
    dns_rules = [x for x in data['dns'].get('rules', []) if not (set(x.get('domain_suffix', [])) == set(HARDBONES) and x.get('server') == 'local')]
    dns_rules.insert(0, {
        "domain_suffix": HARDBONES,
        "server": "local"
    })
    data['dns']['rules'] = dns_rules

    new_rules.insert(0, {
        "outbound": "direct",
        "domain_suffix": HARDBONES
    })
    
    new_rules.insert(1, {
        "outbound": "direct",
        "ip_cidr": ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10", "::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]
    })
    
    for r in rules:
        outbound = "proxy"
        if r['policy'] == 'DIRECT':
            outbound = "direct"
        elif r['policy'] == 'REJECT':
            outbound = "block"
            
        if r['type'].upper() == 'MATCH':
            data['route']['final'] = outbound
            continue
            
        rule_obj = {"outbound": outbound}
        rt = r['type'].upper()
        
        if rt == 'DOMAIN':
            rule_obj['domain'] = [r['payload']]
        elif rt == 'DOMAIN-SUFFIX':
            rule_obj['domain_suffix'] = [r['payload']]
        elif rt == 'DOMAIN-KEYWORD':
            rule_obj['domain_keyword'] = [r['payload']]
        elif rt == 'IP-CIDR' or rt == 'IP-CIDR6':
            rule_obj['ip_cidr'] = [r['payload']]
        elif rt == 'GEOIP':
            rule_obj['geoip'] = [r['payload'].lower()]  
        elif rt == 'PROCESS-NAME':
            rule_obj['process_name'] = [r['payload']]
        else:
            continue 
            
        new_rules.append(rule_obj)
        
    data['route']['rules'] = new_rules
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully migrated Sing-box format: {os.path.basename(file_path)}")

def main():
    print("Parsing MD rules...")
    parsed_rules = parse_md_rules(md_path)
    if not parsed_rules:
        print("No rules parsed. Exiting.")
        return
        
    print(f"Parsed {len(parsed_rules)} rules.")
    
    files = {
        "Clash.json": "clash",
        "Clash Meta.json": "clash",
        "Stash.json": "clash",
        "Surge.json": "clash",
        "Surfboard.json": "surfboard",
        "Shadowrocket.json": "shadowrocket",
        "Sing-box.json": "singbox"
    }
    
    for filename, format_type in files.items():
        fp = os.path.join(v2b_dir, filename)
        if not os.path.exists(fp):
            print(f"File not found: {filename}")
            continue
            
        if format_type == "clash":
            process_clash(fp, parsed_rules)
        elif format_type == "surfboard":
            process_surfboard(fp, parsed_rules)
        elif format_type == "shadowrocket":
            process_shadowrocket(fp, parsed_rules)
        elif format_type == "singbox":
            process_singbox(fp, parsed_rules)

if __name__ == '__main__':
    main()
