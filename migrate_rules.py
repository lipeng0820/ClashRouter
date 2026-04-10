import os
import json
import re

# Configuration
MD_PATH = "分流规则参考.md"
V2B_DIR = "v2b"

# "Hardbone" Bypass List
HARDBONES = [
    # Corporate/Intranet (Active Bypass)
    "corp.kuaishou.com", "kuaishou.com", "streamlake.com", "streamlake.ai",
    # Remote Desktop Tools
    "todesk.com", "oray.com", "oray.cn", "sunlogin.net", "sunlogin.com",
    # Main banking and financial services
    "cmbchina.com", "cmbchina.cn", "pingan.com", "pingan.com.cn", "spdb.com.cn",
    "alipayhk.com", "alipay.hk", "hsbc.com.hk", "hsbc.com", "bochk.com", "za.group", "antbank.hk",
    "futunn.com", "futu5.com", "futuhk.com",
    # Alibaba / Taobao / Alipay Ecosystem & Infrastructure (Fix for opendoc/mpaas)
    "alipay.com", "alipay.cn", "alipayobjects.com", "antgroup.com", "amap.com", 
    "taobao.com", "alibaba.com", "alicdn.com", "aliyun.com", "aliyuncdn.com", 
    "tmall.com", "mmstat.com"
]

def parse_md_rules(md_path):
    if not os.path.exists(md_path): return []
    with open(md_path, 'r', encoding='utf-8') as f:
        md_lines = f.readlines()
    
    rules_start = -1
    for i, line in enumerate(md_lines):
        if line.strip() == 'rules:':
            rules_start = i
            break
    if rules_start == -1: return []
    
    parsed_rules = []
    for line in md_lines[rules_start+1:]:
        line = line.strip()
        if not line or not line.startswith('- '): continue
        parts = [p.strip() for p in line[2:].split(',')]
        if len(parts) < 2: continue
        
        rule_type = parts[0].upper()
        policy_raw = parts[1] if rule_type == 'MATCH' else parts[2] if len(parts) > 2 else 'PROXY'
        
        if policy_raw == '🎯 全球直连': policy = 'DIRECT'
        elif policy_raw == '🛑 全球拦截': policy = 'REJECT'
        else: policy = 'PROXY'
        
        payload = parts[1] if rule_type != 'MATCH' else ""
        options = parts[3:] if rule_type != 'MATCH' and len(parts) > 3 else []
        if rule_type == 'MATCH' and len(parts) > 2: options = parts[2:]

        parsed_rules.append({"type": rule_type, "payload": payload, "policy": policy, "options": options})
    return parsed_rules

def process_clash(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 1. First, find important indices
    rules_idx = -1
    dns_idx = -1
    ns_policy_idx = -1
    fake_ip_filter_idx = -1
    
    for i, l in enumerate(lines):
        s = l.strip()
        if s == 'rules:': rules_idx = i
        elif s == 'dns:': dns_idx = i
        elif s == 'nameserver-policy:': ns_policy_idx = i
        elif s == 'fake-ip-filter:': fake_ip_filter_idx = i

    if rules_idx == -1: return

    # 2. Scrub ALL previous hardbone-related lines to prevent 500 duplicates
    # We remove any lines in nameserver-policy and fake-ip-filter that match our hardbones
    # And we remove our injected rules at the top of rules:
    scrubbed = []
    skip_mode = False
    
    # Simple patterns to catch our injections
    hb_patterns = [f'"{hb}"' for hb in HARDBONES] + [f'"+.{hb}"' for hb in HARDBONES] + [f'"*.{hb}"' for hb in HARDBONES]
    
    for i, l in enumerate(lines[:rules_idx+1]):
        s = l.strip()
        # Skip previously injected hardbone lines in maps/lists
        is_hb_line = any(pat in s for pat in hb_patterns)
        if is_hb_line and ("dhcp://system" in s or "- \"*." in s or "- \"+." in s or "- \"" in s):
            continue
        scrubbed.append(l)

    # 3. Re-inject into DNS blocks
    # Logic: If nameserver-policy exists, prepend hardbones. If not, create it under dns.
    # We do a fresh injection.
    final_lines = []
    for l in scrubbed:
        final_lines.append(l)
        if l.strip() == 'nameserver-policy:':
            for hb in HARDBONES:
                final_lines.append(f'    "{hb}": "dhcp://system"\n')
                final_lines.append(f'    "+.{hb}": "dhcp://system"\n')
        if l.strip() == 'fake-ip-filter:':
            for hb in HARDBONES:
                final_lines.append(f'    - "+.{hb}"\n')
                final_lines.append(f'    - "*.{hb}"\n')
                final_lines.append(f'    - "{hb}"\n')

    # 4. Inject Rules
    final_lines.append('\n  # 硬骨头内网放行区 (Highest Priority)\n')
    for hb in HARDBONES:
        final_lines.append(f'  - DOMAIN-SUFFIX,{hb},DIRECT\n')
    
    final_lines.append('\n  # 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        final_lines.append(f'  - IP-CIDR,{cidr},DIRECT\n')

    for r in rules:
        policy = '$app_name' if r['policy'] == 'PROXY' else r['policy']
        if r['type'] == 'MATCH':
            final_lines.append(f"  - MATCH,{policy}\n")
        else:
            opts = f",{','.join(r['options'])}" if r['options'] else ""
            final_lines.append(f"  - {r['type']},{r['payload']},{policy}{opts}\n")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    print(f"Fixed & Migrated Clash: {os.path.basename(file_path)}")

def process_surfboard(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    r_idx = -1
    for i, l in enumerate(lines):
        if l.strip() == '[Rule]': r_idx = i; break
    if r_idx == -1: return

    new_lines = []
    for l in lines[:r_idx+1]:
        if l.startswith('skip-proxy ='):
            curr = l.strip().split('=')[1].strip()
            missing = [hb for hb in HARDBONES if hb not in curr]
            if missing:
                l = f'skip-proxy = {curr}, ' + ', '.join([f'*.{hb}, {hb}' for hb in missing]) + '\n'
        new_lines.append(l)

    new_lines.append('\n# HARDBONES\n')
    for hb in HARDBONES: new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\n')
    for r in rules:
        p = '$app_name' if r['policy'] == 'PROXY' else r['policy']
        if r['type'] == 'MATCH': new_lines.append(f"FINAL,{p}\n")
        else: new_lines.append(f"{r['type']},{r['payload']},{p}\n")
    
    with open(file_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)

def process_shadowrocket(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
    s_idx = -1
    e_idx = -1
    for i, l in enumerate(lines):
        if l.strip() == '[Rule]': s_idx = i
        elif s_idx != -1 and l.strip().startswith('['): e_idx = i; break
    if s_idx == -1: return

    new_lines = []
    for l in lines[:s_idx+1]:
        if l.startswith('skip-proxy ='):
            m = [hb for hb in HARDBONES if hb not in l]
            if m: l = l.strip() + ', ' + ', '.join([f'*.{hb}, {hb}' for hb in m]) + '\n'
        new_lines.append(l)
    
    new_lines.append('\n# HARDBONES\n')
    for hb in HARDBONES: new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\n')
    for r in rules:
        p = 'PROXY' if r['policy'] == 'PROXY' else r['policy']
        if r['type'] == 'MATCH': new_lines.append(f"FINAL,{p}\n")
        else: new_lines.append(f"{r['type']},{r['payload']},{p}\n")
    
    if e_idx != -1: new_lines.extend(lines[e_idx:])
    with open(file_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)

def process_singbox(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        try: data = json.load(f)
        except: return
    
    data.setdefault('dns', {"servers": [], "rules": []})
    if not any(s.get('tag') == 'local' for s in data['dns']['servers']):
        data['dns']['servers'].append({"tag": "local", "address": "local", "detour": "direct"})
    
    # Clean and Re-inject DNS rules
    d_rules = [r for r in data['dns']['rules'] if not (r.get('domain_suffix') == HARDBONES and r.get('server') == 'local')]
    d_rules.insert(0, {"domain_suffix": HARDBONES, "server": "local"})
    data['dns']['rules'] = d_rules

    # Clean and Re-inject Route rules
    r_rules = []
    r_rules.append({"outbound": "direct", "domain_suffix": HARDBONES})
    r_rules.append({"outbound": "direct", "ip_cidr": ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "::1/128", "fc00::/7"]})
    
    for r in rules:
        out = "proxy" if r['policy'] == 'PROXY' else "direct" if r['policy'] == 'DIRECT' else "block"
        if r['type'] == 'MATCH': data['route']['final'] = out; continue
        obj = {"outbound": out}
        t = r['type'].upper()
        if t == 'DOMAIN': obj['domain'] = [r['payload']]
        elif t == 'DOMAIN-SUFFIX': obj['domain_suffix'] = [r['payload']]
        elif t == 'IP-CIDR' or t == 'IP-CIDR6': obj['ip_cidr'] = [r['payload']]
        elif t == 'GEOIP': obj['geoip'] = [r['payload'].lower()]
        else: continue
        r_rules.append(obj)
    
    data['route']['rules'] = r_rules
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    parsed = parse_md_rules(MD_PATH)
    if not parsed: return
    formats = {"Clash.json": "clash", "Clash Meta.json": "clash", "Stash.json": "clash", "Surge.json": "clash",
               "Surfboard.json": "surfboard", "Shadowrocket.json": "shadowrocket", "Sing-box.json": "singbox"}
    for fn, fmt in formats.items():
        fp = os.path.join(V2B_DIR, fn)
        if not os.path.exists(fp): continue
        if fmt == "clash": process_clash(fp, parsed)
        elif fmt == "surfboard": process_surfboard(fp, parsed)
        elif fmt == "shadowrocket": process_shadowrocket(fp, parsed)
        elif fmt == "singbox": process_singbox(fp, parsed)

if __name__ == '__main__': main()
