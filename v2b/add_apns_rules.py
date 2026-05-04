import os
import re

base_dir = '/Users/lipeng0820/Downloads/ClashRouter/v2b'

# ── Apple Push rules ────────────────────────────────────────────────────────
APNS_DOMAINS = [
    'push.apple.com',
    'gateway.push.apple.com',
    'api.push.apple.com',
    'sandbox.push.apple.com',
]

# ── Clash-family files (use $app_name) ──────────────────────────────────────
clash_files = ['Clash Meta.json', 'Clash.json', 'Stash.json', 'Surfboard.json', 'Surge.json']

# Build the four rule lines for Clash-family
clash_apns_lines = '\n'.join(
    f'  - DOMAIN-SUFFIX,{d},$app_name' for d in APNS_DOMAINS
)
clash_apns_block = f"""
  # Apple Push Notification Service (APNS) — X/Twitter & TG push
{clash_apns_lines}"""

# Anchor: insert BEFORE the first apple-related DOMAIN rule in the rules section
clash_anchor = '  - DOMAIN,tv.apple.com,'

for fname in clash_files:
    path = os.path.join(base_dir, fname)
    if not os.path.exists(path):
        print(f'Skip (not found): {fname}')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'push.apple.com' in content:
        print(f'Already has push rules: {fname}')
        continue

    # Find anchor line and insert before it
    idx = content.find(clash_anchor)
    if idx == -1:
        print(f'Anchor not found in {fname}, skipping')
        continue

    # Find the start of that line (back to the newline before it)
    line_start = content.rfind('\n', 0, idx) + 1
    new_content = content[:line_start] + clash_apns_block + '\n' + content[line_start:]

    # Also fix nameserver-policy for Clash Meta: override +.apple.com dhcp with DoH for push
    if fname == 'Clash Meta.json':
        dns_anchor = '    "apple.com": "dhcp://system"'
        apns_dns_block = (
            '    "push.apple.com": "https://dns.cloudflare.com/dns-query"\n'
            '    "+.push.apple.com": "https://dns.cloudflare.com/dns-query"\n'
        )
        if 'push.apple.com' not in new_content:
            dns_idx = new_content.find(dns_anchor)
            if dns_idx != -1:
                dns_line_start = new_content.rfind('\n', 0, dns_idx) + 1
                new_content = new_content[:dns_line_start] + apns_dns_block + new_content[dns_line_start:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Updated {fname}')

# ── Shadowrocket ─────────────────────────────────────────────────────────────
sr_path = os.path.join(base_dir, 'Shadowrocket.json')
sr_anchor = 'DOMAIN,tv.apple.com,PROXY'

sr_apns_lines = '\n'.join(
    f'DOMAIN-SUFFIX,{d},PROXY' for d in APNS_DOMAINS
)
sr_apns_block = f"""# Apple Push Notification Service (APNS) — X/Twitter & TG push
{sr_apns_lines}"""

if os.path.exists(sr_path):
    with open(sr_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'push.apple.com' in content:
        print('Already has push rules: Shadowrocket.json')
    else:
        idx = content.find(sr_anchor)
        if idx == -1:
            print('Anchor not found in Shadowrocket.json')
        else:
            line_start = content.rfind('\n', 0, idx) + 1
            new_content = content[:line_start] + sr_apns_block + '\n' + content[line_start:]
            with open(sr_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print('Updated Shadowrocket.json')
else:
    print('Shadowrocket.json not found')

