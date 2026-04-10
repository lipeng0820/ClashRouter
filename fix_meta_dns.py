with open("migrate_rules.py", "r") as f:
    code = f.read()

# Replace the injected "system" string with "dhcp://system" for hardbones
# We only want to replace the hardbone injections, not anything else that might legitimately be "system".
import re

new_code = code.replace(
    f'new_lines.insert(ns_idx + 1, f"    \\"+.{{hb}}\\": \\"system\\"\\n")',
    f'new_lines.insert(ns_idx + 1, f"    \\"+.{{hb}}\\": \\"dhcp://system\\"\\n")'
)
new_code = new_code.replace(
    f'new_lines.insert(ns_idx + 1, f"    \\"{{hb}}\\": \\"system\\"\\n")',
    f'new_lines.insert(ns_idx + 1, f"    \\"{{hb}}\\": \\"dhcp://system\\"\\n")'
)

new_code = new_code.replace(
    f'new_lines.insert(dns_idx + 2, f"    \\"+.{{hb}}\\": \\"system\\"\\n")',
    f'new_lines.insert(dns_idx + 2, f"    \\"+.{{hb}}\\": \\"dhcp://system\\"\\n")'
)
new_code = new_code.replace(
    f'new_lines.insert(dns_idx + 2, f"    \\"{{hb}}\\": \\"system\\"\\n")',
    f'new_lines.insert(dns_idx + 2, f"    \\"{{hb}}\\": \\"dhcp://system\\"\\n")'
)

with open("migrate_rules.py", "w") as f:
    f.write(new_code)
