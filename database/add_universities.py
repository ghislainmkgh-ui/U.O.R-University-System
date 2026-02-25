"""Script pour ajouter/mettre à jour les universités partenaires"""
import mysql.connector

def add_partner_universities():
    """Ajoute des universités partenaires dans la base de données"""
    try:
        print("=" * 70)
        print("AJOUT DES UNIVERSITÉS PARTENAIRES")
        print("=" * 70)
        
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="uor_university"
        )
        
        cursor = conn.cursor()
        
        # Universités partenaires à ajouter/mettre à jour
        universities = [
            {
                'university_code': 'UNIKIN',
                'university_name': 'Université de Kinshasa',
                'country': 'République Démocratique du Congo',
                'city': 'Kinshasa',
                'contact_email': 'transfer@unikin.cd',
                'trust_level': 'VERIFIED',
                'is_active': True
            },
            {
                'university_code': 'UPC',
                'university_name': 'Université Protestante au Congo',
                'country': 'République Démocratique du Congo',
                'city': 'Kinshasa',
                'contact_email': 'transfer@upc.cd',
                'trust_level': 'VERIFIED',
                'is_active': True
            },
            {
                'university_code': 'UPN',
                'university_name': 'Université Pédagogique Nationale',
                'country': 'République Démocratique du Congo',
                'city': 'Kinshasa',
                'contact_email': 'transfer@upn.cd',
                'trust_level': 'VERIFIED',
                'is_active': True
            },
            {
                'university_code': 'ISC',
                'university_name': 'Institut Supérieur de Commerce',
                'country': 'République Démocratique du Congo',
                'city': 'Kinshasa',
                'contact_email': 'transfer@isc.cd',
                'trust_level': 'PENDING',
                'is_active': True
            },
            {
                'university_code': 'UNIDOUALA',
                'university_name': 'Université de Douala',
                'country': 'Cameroun',
                'city': 'Douala',
                'contact_email': 'transfer@unidouala.cm',
                'trust_level': 'VERIFIED',
                'is_active': True
            },
            {
                'university_code': 'UY1',
                'university_name': 'Université de Yaoundé I',
                'country': 'Cameroun',
                'city': 'Yaoundé',
                'contact_email': 'transfer@uy1.cm',
                'trust_level': 'VERIFIED',
                'is_active': True
            }
        ]
        
        print(f"\n📍 Mise à jour de {len(universities)} universités partenaires...\n")
        
        added = 0
        updated = 0
        
        for uni in universities:
            # Vérifier si elle existe
            cursor.execute(
                "SELECT id FROM partner_university WHERE university_code = %s",
                (uni['university_code'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Mettre à jour
                cursor.execute("""
                    UPDATE partner_university 
                    SET university_name = %s, country = %s, city = %s, 
                        contact_email = %s, is_active = %s, trust_level = %s
                    WHERE university_code = %s
                """, (uni['university_name'], uni['country'], uni['city'], 
                      uni['contact_email'], uni['is_active'], uni['trust_level'], 
                      uni['university_code']))
                print(f"✏️  {uni['university_code']:12} - {uni['university_name']}")
                updated += 1
            else:
                # Ajouter
                cursor.execute("""
                    INSERT INTO partner_university 
                    (university_code, university_name, country, city, contact_email, is_active, trust_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (uni['university_code'], uni['university_name'], uni['country'], 
                      uni['city'], uni['contact_email'], uni['is_active'], uni['trust_level']))
                print(f"✅ {uni['university_code']:12} - {uni['university_name']}")
                added += 1
        
        conn.commit()
        
        # Vérifier le total
        cursor.execute("SELECT COUNT(*) FROM partner_university")
        total = cursor.fetchone()[0]
        
        # Lister les universités
        cursor.execute("SELECT university_code, university_name, trust_level FROM partner_university ORDER BY university_code")
        universities_list = cursor.fetchall()
        
        print(f"\n" + "=" * 70)
        print(f"✅ Ajoutées: {added}")
        print(f"✏️  Mises à jour: {updated}")
        print(f"📊 Total universités: {total}\n")
        
        print("📚 Universités partenaires actuelles:")
        for code, name, trust in universities_list:
            print(f"   • {code:12} - {name:40} ({trust})")
        
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_partner_universities()
