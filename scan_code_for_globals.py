import os
import re

# Motifs à chercher (ajoute-en d'autres si besoin)
PATTERNS = [
    r'pytmx\.load_pygame',
    r'pygame\.image\.load',
    r'\bMap\s*\(',
]

EXCLUDED_DIRS = {'venv', '.venv', '__pycache__'}

def is_inside_function_or_class(lines, idx):
    # Vérifie si une ligne est indentée (donc à l'intérieur d'une def/class)
    line = lines[idx]
    return line.startswith(' ') or line.startswith('\t')

def scan_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        for pattern in PATTERNS:
            if re.search(pattern, line):
                if not is_inside_function_or_class(lines, i):
                    print(f"\n[SUSPECT] {os.path.relpath(path)} : L{i+1} => {line.strip()}")

def main():
    root = '.'
    for dirpath, dirnames, filenames in os.walk(root):
        # Ignore venv et __pycache__
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for file in filenames:
            if file.endswith('.py'):
                scan_file(os.path.join(dirpath, file))

if __name__ == '__main__':
    print("Scan des appels suspects hors fonction/classe dans tous les .py…")
    main()
    print("\nSCAN TERMINÉ.")

