# Base de Données Reconnaissance Faciale pour Système Accès Porte ESP32
# Ce fichier contient les encodages de visages des utilisateurs autorisés

import json
import time

class FaceDatabase:
    def __init__(self, filename="face_database.json"):
        self.filename = filename
        self.known_faces = []
        self.load_database()

    def load_database(self):
        """Charger les encodages de visages depuis le fichier"""
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.known_faces = data.get('faces', [])
        except:
            print("Aucune base de données faciale existante trouvée, démarrage vide")
            self.known_faces = []

    def save_database(self):
        """Sauvegarder les encodages de visages dans le fichier"""
        data = {'faces': self.known_faces}
        with open(self.filename, 'w') as f:
            json.dump(data, f)

    def add_face(self, face_encoding, user_name="Inconnu"):
        """Ajouter un nouveau visage à la base de données"""
        face_data = {
            'encoding': face_encoding,
            'name': user_name,
            'timestamp': time.time()
        }
        self.known_faces.append(face_data)
        self.save_database()

    def remove_face(self, index):
        """Supprimer un visage de la base de données"""
        if 0 <= index < len(self.known_faces):
            del self.known_faces[index]
            self.save_database()

    def get_face_encodings(self):
        """Obtenir la liste des encodages de visages pour la reconnaissance"""
        return [face['encoding'] for face in self.known_faces]

    def get_face_names(self):
        """Obtenir la liste des noms de visages"""
        return [face['name'] for face in self.known_faces]

# Exemple d'utilisation pour l'entraînement:
# 1. Capturer des images de visages
# 2. Générer des encodages
# 3. Ajouter à la base de données

def train_face_database():
    """Fonction exemple pour entraîner la base de données faciale"""
    db = FaceDatabase()

    # Cela serait remplacé par une capture et encodage de visage réels
    # Pour démonstration, nous ajoutons des données mockées
    mock_encodings = [
        [0.1, 0.2, 0.3] * 42,  # Encodage 128D mocké
        [0.4, 0.5, 0.6] * 42,
    ]

    for i, encoding in enumerate(mock_encodings):
        db.add_face(encoding, f"Utilisateur_{i+1}")

    print(f"Visages entraînés: {len(db.known_faces)}")

if __name__ == "__main__":
    train_face_database()