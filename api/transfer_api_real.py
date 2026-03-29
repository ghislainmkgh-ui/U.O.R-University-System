"""
API REST pour la Communication Inter-Universitaire
Exemple d'implémentation pour U.O.R - Utilise le vrai TransferService
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import logging
import sys
import os

# Ajouter le répertoire parent au path pour pouvoir importer les modules de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.transfer.transfer_service import TransferService
from config.settings import SECRET_KEY

# Configuration basique du logger pour affichage console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = SECRET_KEY
app.config['API_VERSION'] = 'v1'

transfer_service = TransferService()

# ==================== AUTHENTICATION ====================

def generate_api_token(university_code, secret_key):
    """Génère un token JWT pour une université partenaire"""
    payload = {
        'university_code': university_code,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')

def require_api_key(f):
    """Décorateur pour vérifier l'authentification API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Récupérer le token du header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Format: "Bearer <token>"
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid authorization header format'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'API token is missing'
            }), 401
        
        try:
            # Vérifier le token
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.university_code = payload['university_code']
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': 'Invalid token'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== ENDPOINTS ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Endpoint de santé pour vérifier que l'API est accessible"""
    return jsonify({
        'status': 'healthy',
        'service': 'U.O.R Transfer API (Real Service)',
        'version': app.config['API_VERSION'],
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/v1/auth/token', methods=['POST'])
def get_token():
    """
    Génère un token d'authentification pour une université partenaire
    Nécessite : university_code, api_key
    """
    data = request.get_json()
    
    if not data or 'university_code' not in data or 'api_key' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: university_code, api_key'
        }), 400
    
    university_code = data['university_code']
    api_key = data['api_key']
    
    # TODO: Vérifier l'api_key dans la base de données
    # Pour l'instant, accepter toutes les requêtes (DANGEREUX EN PRODUCTION!)
    
    token = generate_api_token(university_code, app.config['SECRET_KEY'])
    
    logger.info(f"Token généré pour {university_code}")
    
    return jsonify({
        'success': True,
        'token': token,
        'expires_in': 86400,  # 24 heures en secondes
        'token_type': 'Bearer'
    }), 200

@app.route('/api/v1/transfer/receive', methods=['POST'])
@require_api_key
def receive_transfer():
    """
    Reçoit une demande de transfert d'une autre université
    Corps : Package de transfert complet (JSON)
    """
    try:
        transfer_data = request.get_json()
        
        if not transfer_data:
            return jsonify({
                'success': False,
                'error': 'No transfer data provided'
            }), 400
        
        # Valider les données
        required_fields = ['transfer_metadata', 'student_info', 'academic_records']
        for field in required_fields:
            if field not in transfer_data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        logger.info(f"🔄 Réception d'un package de transfert depuis {transfer_data.get('transfer_metadata', {}).get('source_university', 'Unknown')}")
        logger.info(f"📦 Données reçues: {len(transfer_data.get('academic_records', {}).get('records', []))} notes académiques")
        
        # Créer la demande de transfert
        success, result = transfer_service.receive_transfer_request(
            transfer_data=transfer_data,
            target_promotion_id=None  # L'admin sélectionnera plus tard
        )
        
        if success:
            logger.info(f"✅ Demande de transfert reçue avec succès: {result}")
            
            return jsonify({
                'success': True,
                'request_code': result,
                'message': 'Transfer request received and pending review',
                'status': 'PENDING_REVIEW'
            }), 201
        else:
            logger.error(f"❌ Échec de réception du transfert: {result}")
            
            return jsonify({
                'success': False,
                'error': result
            }), 400
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la réception du transfert: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/v1/transfer/send', methods=['POST'])
@require_api_key
def send_transfer():
    """
    Envoie un package de transfert vers une autre université
    Corps : { "student_id": 123, "destination_university_code": "UNIKIN" }
    """
    try:
        data = request.get_json()
        
        if not data or 'student_id' not in data or 'destination_university_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: student_id, destination_university_code'
            }), 400
        
        student_id = data['student_id']
        destination_code = data['destination_university_code']
        include_documents = data.get('include_documents', True)
        
        logger.info(f"📤 Préparation du package de transfert pour l'étudiant ID: {student_id} vers {destination_code}")
        
        # Préparer le package
        package = transfer_service.prepare_student_transfer_package(
            student_id=student_id,
            include_documents=include_documents
        )
        
        if not package:
            return jsonify({
                'success': False,
                'error': 'Failed to prepare transfer package - Student not found or data incomplete'
            }), 500
        
        logger.info(f"✅ Package préparé: {package['academic_records']['total_courses']} cours, {package['documents']['total_documents']} documents")
        
        return jsonify({
            'success': True,
            'transfer_code': package['transfer_metadata']['transfer_code'],
            'package': package,
            'message': 'Transfer package prepared successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi du transfert: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/v1/transfer/status/<transfer_code>', methods=['GET'])
@require_api_key
def get_transfer_status(transfer_code):
    """Récupère le statut d'un transfert"""
    try:
        # TODO: Implémenter la récupération du statut depuis la base de données
        
        logger.info(f"📊 Statut demandé pour transfert {transfer_code}")
        
        return jsonify({
            'success': True,
            'transfer_code': transfer_code,
            'status': 'PENDING',
            'message': 'Status check not yet implemented'
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du statut: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/v1/universities', methods=['GET'])
@require_api_key
def list_partner_universities():
    """Liste toutes les universités partenaires"""
    try:
        conn = transfer_service.db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT university_name, university_code, country, city, trust_level
            FROM partner_university
            WHERE is_active = TRUE
            ORDER BY university_name
        """
        cursor.execute(query)
        partners = cursor.fetchall()
        
        cursor.close()
        transfer_service.db.close_connection(conn)
        
        return jsonify({
            'success': True,
            'count': len(partners),
            'universities': partners
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des universités: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ==================== STARTUP ====================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info(" 🚀 Démarrage de l'API de transfert U.O.R (Real Service)")
    logger.info("=" * 70)
    logger.info(f"Version: {app.config['API_VERSION']}")
    logger.info(f"Host: 0.0.0.0:5000")
    logger.info(f"Mode: DEBUG (Development)")
    logger.info("=" * 70)
    
    # En production, utiliser un serveur WSGI comme Gunicorn
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True  # TEMPORAIRE : pour voir les erreurs
    )
