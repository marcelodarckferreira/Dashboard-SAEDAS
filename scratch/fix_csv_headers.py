import os

data_dir = r"c:\Work\Dev\Python\SAEDAS\app\data"
for filename in os.listdir(data_dir):
    if filename.endswith("Ano.csv"):
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if not lines:
            continue
            
        header = lines[0].strip()
        # Se o header já tem 2026, pula
        if "2026" in header:
            print(f"Skipping {filename} - 2026 already in header")
            continue
            
        # Verifica se a primeira linha de dados tem mais campos que o header
        if len(lines) > 1:
            data_fields = lines[1].strip().split(';')
            header_fields = header.split(';')
            if len(data_fields) > len(header_fields):
                new_header = header.replace(";Total", ";2026;Total")
                lines[0] = new_header + "\n"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"Fixed {filename}")
            else:
                print(f"Skipping {filename} - field count matches header")
        else:
            print(f"Skipping {filename} - no data lines")
