#!/usr/bin/env python3
"""Script de correction intelligent pour fg_color="transparent"
Traite uniquement les CTkFrame() calls, pas les autres contextes.
"""
import os
import re

def fix_file(filepath):
    if not os.path.exists(filepath):
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_count = content.count('fg_color="transparent"')
    
    #  Safe regex: remplace UNIQUEMENT dans les CTkFrame et CTkScrollableFrame calls
    pattern = r'ctk\.CTkFrame\s*\(\s*([^)]*)\s*,\s*fg_color="transparent"'
    def replace_frame(match):
        args_before = match.group(1)
        # Assurez-vous pas de doublon  `)` 
        return f'ctk.CTkFrame(\n                {args_before}'
    
    new_content = re.sub(
        r'fg_color="transparent"(\s*[,\)])',
        r'\1',
        content
    )
    
    new_count = new_content.count('fg_color="transparent"')
    fixed = original_count - new_count
    
    if fixed > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'✓ {filepath}: {fixed} occurrences corrigées')
        return fixed
    else:
        print(f'✓ {filepath}: aucune nouvelle occurrence')
        return 0

files = [
    'ui/screens/admin/admin_dashboard.py',
    'ui/dashboard_helper.py',
    'ui/components/modern_widgets.py',
    'ui/components/modern_loading.py',
    'ui/components/modern_dashboard_components.py',
]

total = 0
for f in files:
    total += fix_file(f)

print(f'\n✓ Total: {total} occurrences corrigées')
