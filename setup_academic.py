import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='')
cur = conn.cursor()
cur.execute('USE uor_university')

# Créer la table academic_year
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS academic_year (
            academic_year_id INT AUTO_INCREMENT PRIMARY KEY,
            year_name VARCHAR(50) NOT NULL UNIQUE,
            threshold_amount DECIMAL(15, 2) NOT NULL,
            final_fee DECIMAL(15, 2) NOT NULL,
            partial_valid_days INT DEFAULT 30,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✅ Table academic_year créée")
except Exception as e:
    print(f"⚠️ academic_year: {e}")

# Créer la table exam_period
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exam_period (
            exam_period_id INT AUTO_INCREMENT PRIMARY KEY,
            academic_year_id INT NOT NULL,
            period_name VARCHAR(100) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✅ Table exam_period créée")
except Exception as e:
    print(f"⚠️ exam_period: {e}")

# Ajouter les colonnes manquantes à finance_profile
try:
    cur.execute("ALTER TABLE finance_profile ADD COLUMN academic_year_id INT DEFAULT NULL")
    print("✅ Colonne academic_year_id ajoutée")
except:
    print("⚠️ academic_year_id existe déjà")

# Insérer une année académique par défaut
try:
    cur.execute("""
        INSERT INTO academic_year (year_name, threshold_amount, final_fee, partial_valid_days, is_active)
        VALUES ('2024-2025', 150000, 250000, 30, TRUE)
    """)
    conn.commit()
    print("✅ Année académique 2024-2025 créée")
except:
    print("⚠️ Année 2024-2025 existe déjà")

# Insérer les périodes d'examens
try:
    cur.execute("SELECT academic_year_id FROM academic_year WHERE year_name = '2024-2025'")
    year_id = cur.fetchone()[0]
    
    periods = [
        ('Session 1 - Janvier 2025', '2025-01-06', '2025-01-17'),
        ('Session 2 - Février 2025', '2025-02-03', '2025-02-14'),
    ]
    
    for period_name, start, end in periods:
        try:
            cur.execute("""
                INSERT INTO exam_period (academic_year_id, period_name, start_date, end_date)
                VALUES (%s, %s, %s, %s)
            """, (year_id, period_name, start, end))
            conn.commit()
            print(f"✅ Période créée: {period_name}")
        except:
            print(f"⚠️ Période {period_name} existe déjà")
except Exception as e:
    print(f"❌ Erreur périodes: {e}")

cur.close()
conn.close()
print("\n✅ Configuration académique prête!")
