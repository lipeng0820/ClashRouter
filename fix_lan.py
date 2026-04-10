with open("migrate_rules.py", "r") as f:
    code = f.read()

# For Clash
lan_clash = r"""
    new_lines.append('\n  # 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        new_lines.append(f'  - IP-CIDR,{cidr},DIRECT\n')
    for cidr6 in ["::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]:
        new_lines.append(f'  - IP-CIDR6,{cidr6},DIRECT\n')
"""

code = code.replace(
    "for hb in HARDBONES:\n        new_lines.append(f'  - DOMAIN-SUFFIX,{hb},DIRECT\\n')",
    "for hb in HARDBONES:\n        new_lines.append(f'  - DOMAIN-SUFFIX,{hb},DIRECT\\n')" + lan_clash,
    1 # only the one in process_clash
)

# For Surfboard
lan_surfboard = r"""
    new_lines.append('\n# 局域网及核心内网放行区 (LAN Bypass)\n')
    for cidr in ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]:
        new_lines.append(f'IP-CIDR,{cidr},DIRECT,no-resolve\n')
    for cidr6 in ["::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]:
        new_lines.append(f'IP-CIDR6,{cidr6},DIRECT,no-resolve\n')
"""

code = code.replace(
    "for hb in HARDBONES:\n        new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\\n')",
    "for hb in HARDBONES:\n        new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\\n')" + lan_surfboard,
    1 # only the one in process_surfboard
)

# For Shadowrocket
code = code.replace(
    "for hb in HARDBONES:\n        new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\\n')",
    "for hb in HARDBONES:\n        new_lines.append(f'DOMAIN-SUFFIX,{hb},DIRECT\\n')" + lan_surfboard
)

# For Singbox
lan_singbox_v4 = '["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "100.64.0.0/10"]'
lan_singbox_v6 = '["::1/128", "fc00::/7", "fe80::/10", "fd00::/8"]'

lan_singbox_code = f"""
    new_rules.insert(1, {{
        "outbound": "direct",
        "ip_cidr": {lan_singbox_v4} + {lan_singbox_v6}
    }})
"""

code = code.replace(
    f"    new_rules.insert(0, {{\n        \"outbound\": \"direct\",\n        \"domain_suffix\": HARDBONES\n    }})",
    f"    new_rules.insert(0, {{\n        \"outbound\": \"direct\",\n        \"domain_suffix\": HARDBONES\n    }})\n" + lan_singbox_code
)

with open("migrate_rules.py", "w") as f:
    f.write(code)

