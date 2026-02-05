import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='')
cur = conn.cursor()
cur.execute('USE uor_university')

# Vérifier les tables
cur.execute("SHOW TABLES")
tables = [t[0] for t in cur.fetchall()]
print("Tables dans la base:", ', '.join(tables))

# Vérifier academic_year
if 'academic_year' in tables:
    cur.execute('SELECT COUNT(*) FROM academic_year')
    count = cur.fetchone()[0]
    print(f'✅ Table academic_year existe avec {count} enregistrements')
else:
    print('❌ Table academic_year manquante')

cur.close()
conn.close()
