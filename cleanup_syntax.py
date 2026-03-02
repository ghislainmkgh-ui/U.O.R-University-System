#!/usr/bin/env python3
"""Final cleanup: fixes double commas and syntax issues"""
import os
import re

def cleanup_file(filepath):
    if not os.path.exists(filepath):
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_len = len(content)
    
    # Fix double commas
    content = re.sub(r',\s*,', ',', content)
    
    # Fix opening paren with immediate comma
    content = re.sub(r'\(\s*,', '(', content)
    
    # Fix closing paren with preceding comma
    content = re.sub(r',\s*\)', ')', content)
    
    # Fix double spaces after comma
    content = re.sub(r',\s{2,}', ', ', content)
    
    if len(content) != original_len:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1
    return 0

files = [
    'ui/screens/admin/admin_dashboard.py',
    'ui/screens/login_screen.py',
    'ui/dashboard_helper.py',
    'ui/components/modern_widgets.py',
    'ui/components/modern_loading.py',
    'ui/components/modern_dashboard_components.py',
]

for f in files:
    if cleanup_file(f):
        print(f'✓ {f}: cleanup applied')
    else:
        print(f'✓ {f}: no changes needed')
