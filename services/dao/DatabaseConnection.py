import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement pour la confidentialité 
load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._connection = None
        return cls._instance

    def connect(self):
        """Établit une connexion sécurisée à la base de données."""
        if self._connection is None or not self._connection.is_connected():
            try:
                self._connection = mysql.connector.connect(
                    host=os.getenv("DB_HOST"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    database=os.getenv("DB_NAME"),
     
                    port=int(os.getenv("DB_PORT", 3306))
                )
                print("Connexion à la base de données réussie.")
            except Error as e:
                print(f"Erreur de connexion sécurisée : {e}")
                self._connection = None
        return self._connection

    def close_connection(self):
        """Ferme la connexion proprement pour éviter les fuites de données."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            print("Connexion fermée.")