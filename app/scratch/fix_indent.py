import sys
import os

# Check current directory
print(f"Current Directory: {os.getcwd()}")

file_path = 'app_pages/home.py'
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    sys.exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Python lines are 0-indexed here, so line 1424 is index 1423
    if i >= 1423 and i <= 1542:
        if line.startswith('        '):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Successfully dedented lines 1424 to 1543 in {file_path}")
