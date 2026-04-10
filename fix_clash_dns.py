with open("migrate_rules.py", "r") as f:
    code = f.read()

# We need to inject nameserver-policy in process_clash
injection_code = """
    # 注入 nameserver-policy (重要！内网域名在Clash内必须指定system解析，否则223.5.5.5无法解析内网导致直接失败)
    ns_idx = -1
    for idx, l in enumerate(new_lines):
        if l.strip() == 'nameserver-policy:':
            ns_idx = idx
            break
            
    if ns_idx != -1:
        existing_ns = ''.join(lines[:rules_start+1])
        for hb in HARDBONES:
            if hb not in existing_ns:
                new_lines.insert(ns_idx + 1, f"    \\"+.{hb}\\": \\"system\\"\\n")
                new_lines.insert(ns_idx + 1, f"    \\"{hb}\\": \\"system\\"\\n")
    else:
        dns_idx = -1
        for idx, l in enumerate(new_lines):
            if l.strip() == 'dns:':
                dns_idx = idx
                break
        if dns_idx != -1:
            new_lines.insert(dns_idx + 1, "  nameserver-policy:\\n")
            for hb in HARDBONES:
                new_lines.insert(dns_idx + 2, f"    \\"+.{hb}\\": \\"system\\"\\n")
                new_lines.insert(dns_idx + 2, f"    \\"{hb}\\": \\"system\\"\\n")

    # original append rules
"""

# Replace in process_clash
# We will inject right before replacing fake-ip-filter
old_code = """        if l.strip() == 'fake-ip-filter:':
            for hb in HARDBONES:
                if hb not in existing_fake:
                    new_lines.append(f"    - \\"*.{hb}\\"\\n")
                    new_lines.append(f"    - \\"{hb}\\"\\n")"""

new_code = old_code + "\n" + injection_code

# Wait, the injection code works on new_lines which might be iterating at the same time? No, the loop for fake-ip-filter is first, and it builds new_lines.
# Then after `for l in lines[:rules_start+1]:`, new_lines is fully built.
