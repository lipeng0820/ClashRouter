import os
import json
import re

# Configuration
MD_PATH = "分流规则参考.md"
V2B_DIR = "v2b"
CUSTOM_DIRECT_DOMAINS_PATH = "custom_direct_domains.txt"
CUSTOM_PROXY_DOMAINS_PATH = "custom_proxy_domains.txt"

def load_custom_direct_domains(file_path):
    if not os.path.exists(file_path):
        return []
    domains = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip().lower()
            if not s or s.startswith("#"):
                continue
            s = s.lstrip(".")
            if re.fullmatch(r"[a-z0-9.-]+", s):
                domains.append(s)
    # Stable order + deduplication
    return sorted(set(domains))

def load_custom_proxy_domains(file_path):
    if not os.path.exists(file_path):
        return []
    domains = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip().lower()
            if not s or s.startswith("#"):
                continue
            s = s.lstrip(".")
            if re.fullmatch(r"[a-z0-9.-]+", s):
                domains.append(s)
    return sorted(set(domains))

# "Hardbone" Bypass List (Injected at the very top of rules and handled as High Priority)
HARDBONES = [
    "corp.kuaishou.com", "kuaishou.com", "streamlake.com", "streamlake.ai",
    "todesk.com", "oray.com", "oray.cn", "sunlogin.net", "sunlogin.com",
    "cmbchina.com", "cmbchina.cn", "pingan.com", "pingan.com.cn", "spdb.com.cn",
    "alipayhk.com", "alipay.hk", "hsbc.com.hk", "hsbc.com", "bochk.com", "za.group", "antbank.hk",
    "futunn.com", "futu5.com", "futuhk.com",
    "alipay.com", "alipay.cn", "alipayobjects.com", "antgroup.com", "amap.com", 
    "taobao.com", "alibaba.com", "alicdn.com", "aliyun.com", "aliyuncdn.com", 
    "tmall.com", "mmstat.com"
]

# Compatibility direct list for domestic .com sites that may be misrouted under fake-ip/TUN.
DEFAULT_FORCE_DIRECT_DOMAINS = [
    "aigei.com",
]
FORCE_DIRECT_DOMAINS = sorted(set(DEFAULT_FORCE_DIRECT_DOMAINS + load_custom_direct_domains(CUSTOM_DIRECT_DOMAINS_PATH)))

# Reliability proxy list (speed-priority default keeps this minimal).
DEFAULT_FORCE_PROXY_DOMAINS = [
    "900820.xyz",
    "googleapis.com", 
    "googleusercontent.com",
    "github.com",
    "telegram.org",
    "run.app"
]
FORCE_PROXY_DOMAINS = sorted(set(DEFAULT_FORCE_PROXY_DOMAINS + load_custom_proxy_domains(CUSTOM_PROXY_DOMAINS_PATH)))

# Exact-host overrides (higher precision than suffix rules).
FORCE_PROXY_EXACT_DOMAINS = [
    "x.900820.xyz",
]

# For Clash-family outputs, forced-proxy domains should bypass user select group
# (which may currently point to DIRECT) and always use an actual proxy group.
FORCED_PROXY_POLICY_CLASH = "$app_name"

# If Cloudflare/Google DoH is not reachable locally, Google-family DNS resolution may timeout.
# Rewrite these to a reachable domestic DoH for stability.
DNS_POLICY_REWRITE = {
    "+.google.com": "https://doh.pub/dns-query",
    "+.googleapis.com": "https://doh.pub/dns-query",
    "+.googleapis.cn": "https://doh.pub/dns-query",
    "+.googlevideo.com": "https://doh.pub/dns-query",
    "+.gstatic.com": "https://doh.pub/dns-query",
}

# Kernel-level Bypass Domains (Injected into skip-proxy/fake-ip-filter to bypass VPN tunnel entirely)
BYPASS_DOMAINS = [
    "apple.com", "icloud.com", "itunes.apple.com", "mzstatic.com", 
    "aaplimg.com", "cdn-apple.com", "apple-dns.net", "ls.apple.com"
] + HARDBONES + FORCE_DIRECT_DOMAINS

# Smart Overrides: Force specific policies regardless of source file conflicts
SMART_OVERRIDES = {
    # Apple ecosystem: Direct for infrastructure, Proxy for News/Media
    "apple.com": "DIRECT",
    "icloud.com": "DIRECT",
    "itunes.apple.com": "DIRECT",
    "mzstatic.com": "DIRECT",
    "aaplimg.com": "DIRECT",
    "apple-cloudkit.com": "DIRECT",
    "apple.co": "DIRECT",
    "cdn-apple.com": "DIRECT",
    "appleid.apple.com": "DIRECT",
    "developer.apple.com": "DIRECT",
    "apple.news": "PROXY",
    "news-assets.apple.com": "PROXY",
    "news-events.apple.com": "PROXY",
    "tv.apple.com": "PROXY",
    # Microsoft
    "outlook.com": "DIRECT",
    "hotmail.com": "DIRECT",
    "windowsupdate.com": "DIRECT",
    "office.com": "DIRECT",
    # Media
    "bilibili.com": "DIRECT",
    "hdslb.com": "DIRECT"
}
for _d in FORCE_DIRECT_DOMAINS:
    SMART_OVERRIDES[_d] = "DIRECT"
for _d in FORCE_PROXY_DOMAINS:
    SMART_OVERRIDES[_d] = "PROXY"
for _d in FORCE_PROXY_EXACT_DOMAINS:
    SMART_OVERRIDES[_d] = "PROXY"

# Shadowrocket: US priority routing chain for Capital One / PayPal / Claude iOS
SR_US_PRIMARY_POLICY = "US 美丽合众"
SR_US_BACKUP_POLICY = "US-其他节点"
SR_US_PRIORITY_POLICY = "US-金融与Claude优先"
SR_US_BACKUP_REGEX = "(?=.*(US|USA|United States|美国))^((?!(美丽合众)).)*$"
SR_US_PRIORITY_RULES = [
    ("DOMAIN-KEYWORD", "capitalone"),
    ("DOMAIN-SUFFIX", "capitalone.com"),
    ("DOMAIN-SUFFIX", "capitalone360.com"),
    ("DOMAIN-SUFFIX", "paypal.com"),
    ("DOMAIN-SUFFIX", "paypal.me"),
    ("DOMAIN-SUFFIX", "paypalobjects.com"),
    ("DOMAIN-SUFFIX", "paypal-mktg.com"),
    ("DOMAIN-SUFFIX", "claude.ai"),
    ("DOMAIN-SUFFIX", "anthropic.com"),
    ("DOMAIN-SUFFIX", "anthropic.ai"),
    ("PROCESS-NAME", "Claude"),
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
    
    rule_dict = {} # (type, payload) -> {policy, weight}
    # Policy weights: REJECT (10) > DIRECT (5) > PROXY (1)
    # If same weight, first occurrence in file wins (though usually they are the same)
    
    for line in md_lines[rules_start+1:]:
        line = line.strip()
        if not line or not line.startswith('- '): continue
        parts = [p.strip() for p in line[2:].split(',')]
        if len(parts) < 2: continue
        
        rule_type = parts[0].upper()
        payload = parts[1] if rule_type != 'MATCH' else "FINAL"
        policy_raw = parts[1] if rule_type == 'MATCH' else parts[2] if len(parts) > 2 else 'PROXY'
        
        if policy_raw == '🎯 全球直连': policy = 'DIRECT'; weight = 5
        elif policy_raw == '🛑 全球拦截': policy = 'REJECT'; weight = 10
        else: policy = 'PROXY'; weight = 1
        
        # Apply Smart Overrides
        for domain, forced_policy in SMART_OVERRIDES.items():
            if payload == domain or payload.endswith("." + domain):
                policy = forced_policy
                weight = 100 # High weight to override everything
                break
        
        key = (rule_type, payload)
        if key not in rule_dict or weight > rule_dict[key]['weight']:
            rule_dict[key] = {"policy": policy, "weight": weight, "options": parts[2:] if rule_type == 'MATCH' else parts[3:] if len(parts) > 3 else []}

    # Conver dictionary back to list and perform "Rule Folding"
    consolidated = []
    # Sort keys: Subdomain rules later, so we can check if they are redundant with a suffix
    sorted_keys = sorted(rule_dict.keys(), key=lambda x: (x[0], len(x[1])))
    
    # Simple folding: If DOMAIN-SUFFIX exists, remove redundant DOMAIN rules with SAME policy
    suffixes = {p: d['policy'] for (t, p), d in rule_dict.items() if t == 'DOMAIN-SUFFIX'}
    
    final_rules = []
    for (rtype, payload) in sorted_keys:
        data = rule_dict[(rtype, payload)]
        # Filtering logic
        if rtype == 'DOMAIN':
            parts = payload.split('.')
            is_redundant = False
            for i in range(1, len(parts)):
                parent = '.'.join(parts[i:])
                if parent in suffixes and suffixes[parent] == data['policy']:
                    is_redundant = True
                    break
            if is_redundant: continue
            
        final_rules.append({"type": rtype, "payload": payload, "policy": data['policy'], "options": data['options']})
        
    return final_rules

def process_clash(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    rules_idx = -1
    for i, l in enumerate(lines):
        s = l.strip()
        if s == 'rules:': rules_idx = i
    
    if rules_idx == -1: return

    # 2. Scrub ALL previous bypass-related lines to prevent duplicates
    scrubbed = []
    
    # Simple patterns to catch our injections
    bypass_patterns = [f'"{d}"' for d in BYPASS_DOMAINS] + [f'"+.{d}"' for d in BYPASS_DOMAINS] + [f'"*.{d}"' for d in BYPASS_DOMAINS]
    
    for i, l in enumerate(lines[:rules_idx+1]):
        s = l.strip()
        # Skip previously injected lines in maps/lists
        is_bypass_line = any(pat in s for pat in bypass_patterns)
        if is_bypass_line and ("dhcp://system" in s or "- \"*." in s or "- \"+." in s or "- \"" in s):
            continue
        scrubbed.append(l)

    # 3. Re-inject into DNS blocks
    final_lines = []
    in_nameserver_policy = False
    for l in scrubbed:
        stripped = l.strip()
        if stripped == 'nameserver-policy:':
            in_nameserver_policy = True
        elif in_nameserver_policy and stripped and not l.startswith('    '):
            in_nameserver_policy = False
        elif in_nameserver_policy:
            m = re.match(r'^(\s*)"([^"]+)":\s*"([^"]+)"\s*$', l.rstrip('\n'))
            if m and m.group(2) in DNS_POLICY_REWRITE:
                l = f'{m.group(1)}"{m.group(2)}": "{DNS_POLICY_REWRITE[m.group(2)]}"\n'

        final_lines.append(l)
        if stripped == 'nameserver-policy:':
            for d in BYPASS_DOMAINS:
                final_lines.append(f'    "{d}": "dhcp://system"\n')
                final_lines.append(f'    "+.{d}": "dhcp://system"\n')
        if stripped == 'fake-ip-filter:':
            for d in BYPASS_DOMAINS:
                final_lines.append(f'    - "+.{d}"\n')
                final_lines.append(f'    - "*.{d}"\n')
                final_lines.append(f'    - "{d}"\n')

    if FORCE_PROXY_EXACT_DOMAINS or FORCE_PROXY_DOMAINS:
        final_lines.append('\n  # 强制代理域名 (Blocked/Unstable on DIRECT)\n')
        for d in FORCE_PROXY_EXACT_DOMAINS:
            final_lines.append(f'  - DOMAIN,{d},{FORCED_PROXY_POLICY_CLASH}\n')
        for d in FORCE_PROXY_DOMAINS:
            final_lines.append(f'  - DOMAIN-SUFFIX,{d},{FORCED_PROXY_POLICY_CLASH}\n')

    if FORCE_DIRECT_DOMAINS:
        final_lines.append('\n  # 兼容性直连域名 (Avoid CN .com Misroute)\n')
        for d in FORCE_DIRECT_DOMAINS:
            final_lines.append(f'  - DOMAIN-SUFFIX,{d},DIRECT\n')

    final_lines.append('\n  # 硬骨头内网放行区 (Highest Priority)\n')
    for hb in HARDBONES: final_lines.append(f'  - DOMAIN-SUFFIX,{hb},DIRECT\n')
    final_lines.append('\n  # 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        final_lines.append(f'  - IP-CIDR,{cidr},DIRECT\n')

    match_policy = '$app_name'
    for r in rules:
        policy = '$app_name' if r['policy'] == 'PROXY' else r['policy']
        if r['type'] == 'MATCH':
            match_policy = policy
            continue
        opts = f",{','.join(r['options'])}" if r['options'] else ""
        final_lines.append(f"  - {r['type']},{r['payload']},{policy}{opts}\n")
    final_lines.append(f"  - MATCH,{match_policy}\n")

    with open(file_path, 'w', encoding='utf-8') as f: f.writelines(final_lines)
    print(f"Migrated & Optimized Clash: {os.path.basename(file_path)}")

def process_surfboard(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
    r_idx = -1
    for i, l in enumerate(lines):
        if l.strip() == '[Rule]': r_idx = i; break
    if r_idx == -1: return
    new_lines = []
    for l in lines[:r_idx+1]:
        if l.startswith('skip-proxy ='):
            curr = l.strip().split('=')[1].strip()
            missing = [d for d in BYPASS_DOMAINS if d not in curr]
            if missing:
                l = f'skip-proxy = {curr}, ' + ', '.join([f'*.{d}, {d}' for d in missing]) + '\n'
        new_lines.append(l)

    if FORCE_PROXY_EXACT_DOMAINS or FORCE_PROXY_DOMAINS:
        new_lines.append('\n# Forced Proxy Domains\n')
        for d in FORCE_PROXY_EXACT_DOMAINS:
            new_lines.append(f'DOMAIN,{d},{FORCED_PROXY_POLICY_CLASH}\n')
        for d in FORCE_PROXY_DOMAINS:
            new_lines.append(f'DOMAIN-SUFFIX,{d},{FORCED_PROXY_POLICY_CLASH}\n')

    if FORCE_DIRECT_DOMAINS:
        new_lines.append('\n# Compatibility Direct Domains\n')
        for d in FORCE_DIRECT_DOMAINS:
            new_lines.append(f'DOMAIN-SUFFIX,{d},DIRECT\n')

    new_lines.append('\n# HARDBONES\n')
    for hb in HARDBONES: new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\n')
    final_policy = '$app_name'
    for r in rules:
        p = '$app_name' if r['policy'] == 'PROXY' else r['policy']
        if r['type'] == 'MATCH':
            final_policy = p
            continue
        new_lines.append(f"{r['type']},{r['payload']},{p}\n")
    new_lines.append(f"FINAL,{final_policy}\n")
    with open(file_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)

def section_bounds(lines, section_name):
    s_idx = -1
    e_idx = -1
    section_header = f'[{section_name}]'
    for i, l in enumerate(lines):
        if l.strip() == section_header:
            s_idx = i
            break
    if s_idx == -1:
        return -1, -1
    e_idx = len(lines)
    for i in range(s_idx + 1, len(lines)):
        if lines[i].strip().startswith('['):
            e_idx = i
            break
    return s_idx, e_idx

def ensure_shadowrocket_proxy_groups(lines):
    p_s_idx, p_e_idx = section_bounds(lines, "Proxy Group")
    r_s_idx, _ = section_bounds(lines, "Rule")

    managed_comment = '# 首选 US 美丽合众，故障后回落其他美国节点，再回落到当前用户选择'
    managed_lines = [
        f'{managed_comment}\n',
        f'{SR_US_BACKUP_POLICY} = fallback, policy-regex-filter={SR_US_BACKUP_REGEX}, interval=300, timeout=5, url=http://www.gstatic.com/generate_204, hidden=1\n',
        f'{SR_US_PRIORITY_POLICY} = fallback, {SR_US_PRIMARY_POLICY}, {SR_US_BACKUP_POLICY}, PROXY, interval=300, timeout=5, url=http://www.gstatic.com/generate_204\n'
    ]
    managed_prefixes = (f'{SR_US_BACKUP_POLICY} =', f'{SR_US_PRIORITY_POLICY} =')

    if p_s_idx == -1:
        insert_idx = r_s_idx if r_s_idx != -1 else len(lines)
        new_lines = lines[:insert_idx]
        if new_lines and new_lines[-1].strip():
            new_lines.append('\n')
        new_lines.append('[Proxy Group]\n')
        new_lines.extend(managed_lines)
        new_lines.append('\n')
        new_lines.extend(lines[insert_idx:])
        return new_lines

    preserved = []
    for l in lines[p_s_idx + 1:p_e_idx]:
        stripped = l.strip()
        if stripped == managed_comment:
            continue
        if any(stripped.startswith(prefix) for prefix in managed_prefixes):
            continue
        preserved.append(l)

    new_lines = lines[:p_s_idx + 1]
    new_lines.extend(managed_lines)
    if preserved and preserved[0].strip():
        new_lines.append('\n')
    new_lines.extend(preserved)
    new_lines.extend(lines[p_e_idx:])
    return new_lines

def process_shadowrocket(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()

    lines = ensure_shadowrocket_proxy_groups(lines)
    s_idx, e_idx = section_bounds(lines, "Rule")
    if s_idx == -1: return

    new_lines = []
    for l in lines[:s_idx+1]:
        if l.startswith('skip-proxy ='):
            m = [d for d in BYPASS_DOMAINS if d not in l]
            if m: l = l.strip() + ', ' + ', '.join([f'*.{d}, {d}' for d in m]) + '\n'
        new_lines.append(l)

    new_lines.append('\n# Capital One / PayPal / Claude iOS App\n')
    for rtype, payload in SR_US_PRIORITY_RULES:
        new_lines.append(f'{rtype},{payload},{SR_US_PRIORITY_POLICY}\n')

    if FORCE_PROXY_EXACT_DOMAINS or FORCE_PROXY_DOMAINS:
        new_lines.append('\n# Forced Proxy Domains\n')
        for d in FORCE_PROXY_EXACT_DOMAINS:
            new_lines.append(f'DOMAIN,{d},PROXY\n')
        for d in FORCE_PROXY_DOMAINS:
            new_lines.append(f'DOMAIN-SUFFIX,{d},PROXY\n')

    if FORCE_DIRECT_DOMAINS:
        new_lines.append('\n# Compatibility Direct Domains\n')
        for d in FORCE_DIRECT_DOMAINS:
            new_lines.append(f'DOMAIN-SUFFIX,{d},DIRECT\n')

    new_lines.append('\n# HARDBONES\n')
    for hb in HARDBONES: new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\n')
    final_policy = 'PROXY'
    for r in rules:
        p = 'PROXY' if r['policy'] == 'PROXY' else r['policy']
        if r['type'] == 'MATCH':
            final_policy = p
            continue
        new_lines.append(f"{r['type']},{r['payload']},{p}\n")
    new_lines.append(f"FINAL,{final_policy}\n")
    if e_idx != -1: new_lines.extend(lines[e_idx:])
    with open(file_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)
    print(f"Migrated & Optimized Shadowrocket: {os.path.basename(file_path)}")

def process_singbox(file_path, rules):
    with open(file_path, 'r', encoding='utf-8') as f:
        try: data = json.load(f)
        except: return
    data.setdefault('dns', {"servers": [], "rules": []})
    if not any(s.get('tag') == 'local' for s in data['dns']['servers']):
        data['dns']['servers'].append({"tag": "local", "address": "local", "detour": "direct"})
    local_suffix = sorted(set(HARDBONES + FORCE_DIRECT_DOMAINS))
    data['dns']['rules'] = [{"domain_suffix": local_suffix, "server": "local"}] + [r for r in data['dns']['rules'] if r.get('server') != 'local']
    r_rules = []
    if FORCE_PROXY_EXACT_DOMAINS or FORCE_PROXY_DOMAINS:
        if FORCE_PROXY_EXACT_DOMAINS:
            r_rules.append({"outbound": "proxy", "domain": FORCE_PROXY_EXACT_DOMAINS})
        r_rules.append({"outbound": "proxy", "domain_suffix": FORCE_PROXY_DOMAINS})
    r_rules.extend([{"outbound": "direct", "domain_suffix": local_suffix}, {"outbound": "direct", "ip_cidr": ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "::1/128"]}])
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
    rules = parse_md_rules(MD_PATH)
    if not rules: return
    print(f"Rules parsed: {len(rules)} (after deduplication and folding)")
    fmts = {"Clash.json": "clash", "Clash Meta.json": "clash", "Stash.json": "clash", "Surge.json": "clash",
            "Surfboard.json": "surfboard", "Shadowrocket.json": "shadowrocket", "Sing-box.json": "singbox"}
    for fn, fmt in fmts.items():
        fp = os.path.join(V2B_DIR, fn)
        if not os.path.exists(fp): continue
        if fmt == "clash": process_clash(fp, rules)
        elif fmt == "surfboard": process_surfboard(fp, rules)
        elif fmt == "shadowrocket": process_shadowrocket(fp, rules)
        elif fmt == "singbox": process_singbox(fp, rules)

if __name__ == '__main__': main()
