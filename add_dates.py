import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='')
cur = conn.cursor()
cur.execute('USE uor_university')

# Ajouter les colonnes start_date et end_date
try:
    cur.execute("ALTER TABLE academic_year ADD COLUMN start_date DATE DEFAULT '2024-09-01' AFTER year_name")
    conn.commit()
    print('✅ Colonne start_date ajoutée')
except Exception as e:
    if 'Duplicate' in str(e):
        print('⚠️ start_date existe déjà')
    else:
        print(f'❌ {e}')

try:
    cur.execute("ALTER TABLE academic_year ADD COLUMN end_date DATE DEFAULT '2025-08-31' AFTER start_date")
    conn.commit()
    print('✅ Colonne end_date ajoutée')
except Exception as e:
    if 'Duplicate' in str(e):
        print('⚠️ end_date existe déjà')
    else:
        print(f'❌ {e}')

cur.close()
conn.close()
