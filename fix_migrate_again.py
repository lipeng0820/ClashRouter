with open("migrate_rules.py", "r") as f:
    code = f.read()

# Instead of complex insertion and skipping, let's just do a brute force replace at the end!
# In process_clash, right before writing `with open(file_path, 'w', encoding='utf-8') as f:`
# We can just run string replace on the whole output buffer!

brute_force = """
    # Brute force fix: if we copied old hardbones, replace them
    joined_lines = "".join(new_lines)
    for hb in HARDBONES:
        joined_lines = joined_lines.replace(f'"{hb}": "system"', f'"{hb}": "dhcp://system"')
        joined_lines = joined_lines.replace(f'"+.{hb}": "system"', f'"+.{hb}": "dhcp://system"')
    
    new_lines = [l + '\\n' for l in joined_lines.split('\\n')[:-1]]
"""

old_code = "    with open(file_path, 'w', encoding='utf-8') as f:"
new_code = brute_force + "\n    with open(file_path, 'w', encoding='utf-8') as f:"

if brute_force not in code:
    code = code.replace(old_code, new_code)

with open("migrate_rules.py", "w") as f:
    f.write(code)

