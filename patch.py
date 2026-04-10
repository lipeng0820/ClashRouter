import re

with open('migrate_rules.py', 'r') as f:
    code = f.read()

# Add process_shadowrocket function after process_surfboard
shadowrocket_func = """
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
        
    new_lines = lines[:rules_start+1]
    
    for r in rules:
        # Shadowrocket policy natively uses PROXY instead of $app_name
        policy = 'PROXY' if r['policy'] == 'PROXY' else r['policy']
        if r['type'].upper() == 'MATCH':
            new_lines.append(f"FINAL,{policy}\\n")
        elif r['type'].upper() == 'IP-CIDR6':
            # Shadowrocket uses IP-CIDR6 correctly
            opt_str = f",{','.join(r['options'])}" if r['options'] else ""
            new_lines.append(f"{r['type']},{r['payload']},{policy}{opt_str}\\n")
        else:
            opt_str = f",{','.join(r['options'])}" if r['options'] else ""
            new_lines.append(f"{r['type']},{r['payload']},{policy}{opt_str}\\n")
            
    new_lines.append("\\n")
    new_lines.extend(lines[rules_end:])
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully migrated Shadowrocket format: {os.path.basename(file_path)}")
"""

code = code.replace('def process_singbox', shadowrocket_func.strip() + '\n\ndef process_singbox')

# Add Shadowrocket.json to files
code = code.replace('"Surfboard.json": "surfboard",', '"Surfboard.json": "surfboard",\n        "Shadowrocket.json": "shadowrocket",')

# Add execution call
execution_call = """
        elif format_type == "surfboard":
            process_surfboard(fp, parsed_rules)
        elif format_type == "shadowrocket":
            process_shadowrocket(fp, parsed_rules)
"""
code = code.replace('elif format_type == "surfboard":\n            process_surfboard(fp, parsed_rules)', execution_call.strip())

with open('migrate_rules.py', 'w') as f:
    f.write(code)

