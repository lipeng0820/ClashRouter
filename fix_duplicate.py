with open("migrate_rules.py", "r") as f:
    code = f.read()

# Fix Surfboard and Shadowrocket duplicate skip-proxy
code = code.replace(
    "append_list = ', '.join([f'*.{d}, {d}' for d in HARDBONES])\n            l = l.strip() + ', ' + append_list + '\\n'",
    "missing = [d for d in HARDBONES if d not in l]\n            if missing:\n                append_list = ', '.join([f'*.{d}, {d}' for d in missing])\n                l = l.strip() + ', ' + append_list + '\\n'"
)
# Fix Clash fake-ip-filter duplicate
code = code.replace(
    "for hb in HARDBONES:\n                new_lines.append(f\"    - \\\"*.{hb}\\\"\\n\")\n                new_lines.append(f\"    - \\\"{hb}\\\"\\n\")",
    "existing_fake = ''.join(lines[:rules_start+1])\n            for hb in HARDBONES:\n                if hb not in existing_fake:\n                    new_lines.append(f\"    - \\\"*.{hb}\\\"\\n\")\n                    new_lines.append(f\"    - \\\"{hb}\\\"\\n\")"
)

with open("migrate_rules.py", "w") as f:
    f.write(code)

