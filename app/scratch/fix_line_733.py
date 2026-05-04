import os

file_path = 'app_pages/home.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Linha 733 é índice 732
if lines[732].strip() == 'st.markdown("---")':
    lines[732] = '    st.markdown("---")\n'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Linha 733 corrigida.")
else:
    print(f"Conteúdo da linha 732 não confere: '{lines[732].strip()}'")
