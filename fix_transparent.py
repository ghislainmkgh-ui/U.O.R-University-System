#!/usr/bin/env python3
"""Script pour corriger tous les fg_color="transparent" """
import os
import re

files = [
    'ui/screens/login_screen.py',
    'ui/screens/login_screen_backup.py',
    'ui/screens/admin/admin_dashboard.py',
    'ui/dashboard_helper.py',
    'ui/components/modern_widgets.py',
    'ui/components/modern_loading.py',
    'ui/components/modern_dashboard_components.py',
]

for filepath in files:
    if not os.path.exists(filepath):
        print(f'Fichier {filepath} non trouvé')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Compter les occurrences
    count = content.count('fg_color="transparent"')
    count2 = content.count("bg_color=\"transparent\"")
    
    # Remplacer les attributs
    new_content = content.replace('fg_color="transparent"', '')
    new_content = new_content.replace('bg_color="transparent"', '')
    
    # Nettoyer les virgules superflues
    new_content = re.sub(r',\s*,', ',', new_content)
    new_content = re.sub(r'\(\s*,', '(', new_content)
    new_content = re.sub(r',\s*\)', ')', new_content)
    new_content = re.sub(r',\s*\n', '\n', new_content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    total = count + count2
    if total > 0:
        print(f'✓ {filepath}: {total} occurrences corrigées (fg_color={count}, bg_color={count2})')
    else:
        print(f'✓ {filepath}: aucune occurrence')

