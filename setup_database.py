#!/usr/bin/env python3
"""
Script pour initialiser la base de données MySQL
"""

import mysql.connector
from pathlib import Path

def setup_database():
    """Crée la base de données et les tables"""
    
    try:
        # Connexion à MySQL (sans spécifier de base de données)
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""  # Pas de mot de passe
        )
        
        cursor = connection.cursor()
        
        # Supprimer la base de données existante
        print("Suppression de la base de données existante...")
        cursor.execute("DROP DATABASE IF EXISTS uor_university")
        connection.commit()
        print("✅ Base de données supprimée")
        
        # Lire le fichier SQL
        sql_file = Path(__file__).parent / "database_schema.sql"
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Exécuter les commandes SQL
        commands = sql_content.split(';')
        
        for command in commands:
            command = command.strip()
            if command:  # Ignorer les lignes vides
                cursor.execute(command)
        
        connection.commit()
        print("✅ Base de données créée avec succès!")
        print("✅ Tables créées avec succès!")
        print("✅ Données de test insérées!")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Erreur MySQL: {err}")
        return False
    except Exception as err:
        print(f"❌ Erreur: {err}")
        return False
    
    return True

if __name__ == "__main__":
    setup_database()
