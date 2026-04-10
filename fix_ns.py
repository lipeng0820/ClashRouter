with open("migrate_rules.py", "r") as f:
    code = f.read()

old_code = """    if ns_idx != -1:
        existing_ns = ''.join(lines[:rules_start+1])
        for hb in HARDBONES:
            if hb not in existing_ns:
                new_lines.insert(ns_idx + 1, f"    \\"+.{hb}\\": \\"system\\"\\n")
                new_lines.insert(ns_idx + 1, f"    \\"{hb}\\": \\"system\\"\\n")"""

new_code = """    if ns_idx != -1:
        # Check if already injected specifically in nameserver-policy
        # The easiest way is just check 10 lines ahead
        check_str = ''.join(new_lines[ns_idx:ns_idx+10])
        for hb in HARDBONES:
            if f'"+.{hb}"' not in check_str:
                new_lines.insert(ns_idx + 1, f"    \\"+.{hb}\\": \\"system\\"\\n")
                new_lines.insert(ns_idx + 1, f"    \\"{hb}\\": \\"system\\"\\n")"""

if old_code in code:
    code = code.replace(old_code, new_code)
else:
    print("Old code not found!")

# Same for dns check
old_dns = """        if dns_idx != -1:
            new_lines.insert(dns_idx + 1, "  nameserver-policy:\\n")
            for hb in HARDBONES:
                new_lines.insert(dns_idx + 2, f"    \\"+.{hb}\\": \\"system\\"\\n")
                new_lines.insert(dns_idx + 2, f"    \\"{hb}\\": \\"system\\"\\n")"""

new_dns = """        if dns_idx != -1:
            if "nameserver-policy" not in ''.join(new_lines):
                new_lines.insert(dns_idx + 1, "  nameserver-policy:\\n")
                for hb in HARDBONES:
                    new_lines.insert(dns_idx + 2, f"    \\"+.{hb}\\": \\"system\\"\\n")
                    new_lines.insert(dns_idx + 2, f"    \\"{hb}\\": \\"system\\"\\n")"""

if old_dns in code:
    code = code.replace(old_dns, new_dns)

with open("migrate_rules.py", "w") as f:
    f.write(code)

