import os
import re

files_to_fix = ['Surge.json', 'Clash.json', 'Stash.json', 'Surfboard.json', 'Clash Meta.json']
directories = ['/Users/lipeng0820/Downloads/ClashRouter/v2b']

keywords = ['google', 'bing', 'openai', 'chatgpt', 'claude', 'anthropic', 'gemini', 'perplexity']

# Regex matches lines containing any of the keywords and ending with ,$app_name
pattern = re.compile(r'^(.*?(' + '|'.join(keywords) + r').*?)(,\$app_name)([\s\r\n]*)$', re.IGNORECASE)

for fp in files_to_fix:
    path = os.path.join(directories[0], fp)
    if not os.path.exists(path):
        print(f"Skipping {path}, file not found.")
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    changed_count = 0
    for line in lines:
        new_line = pattern.sub(r'\1,AI固定出口\4', line)
        if new_line != line:
            changed_count += 1
        new_lines.append(new_line)
        
    if changed_count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Fixed {changed_count} lines in {fp}")
    else:
        print(f"No changes needed for {fp}")
