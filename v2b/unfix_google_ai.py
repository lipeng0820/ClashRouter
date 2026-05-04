import os
import re

directories = ['/Users/lipeng0820/Downloads/ClashRouter/v2b']
keywords = ['google', 'gemini', 'bard']

# We will check all json files in the directory
for filename in os.listdir(directories[0]):
    if not filename.endswith('.json'):
        continue
    
    path = os.path.join(directories[0], filename)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    changed_count = 0
    
    # Decide replacement target
    # Shadowrocket usually uses PROXY, others use $app_name
    replacement = ',PROXY' if 'Shadowrocket' in filename else ',$app_name'
    
    for line in lines:
        lower_line = line.lower()
        if any(kw in lower_line for kw in keywords) and ',AI固定出口' in line:
            new_line = line.replace(',AI固定出口', replacement)
            changed_count += 1
            new_lines.append(new_line)
        else:
            new_lines.append(line)
            
    if changed_count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Reverted {changed_count} lines in {filename} (changed to {replacement})")
    else:
        print(f"No changes needed for {filename}")

