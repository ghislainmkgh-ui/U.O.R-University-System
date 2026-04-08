"""
Serveur d'Accès U.O.R — access_server.py
=========================================
Reçoit les requêtes HTTP POST de l'ESP32 (validation code + reconnaissance faciale).
Lance la reconnaissance faciale via la caméra IP sur signal de l'ESP32.

NOUVELLE ARCHITECTURE (sans ESP32-CAM, sans Arduino) :
  ESP32 (clavier + servo)
      └─ HTTP POST /verify_code {"code": "XXXX"}
              └─ access_server.py (ce fichier)
                      ├─ Valide le code en base de données
                      ├─ Capture une image depuis la caméra IP (RTSP ou HTTP snapshot)
                      ├─ Reconnaissance faciale (face_recognition + OpenCV)
                      └─ Retourne {"access": "granted|denied", "name": "...", "reason": "..."}

DÉMARRAGE :
  python access_server.py
  ou en production :
  python access_server.py --host 0.0.0.0 --port 5050

CONFIGURATION :
  Voir config/settings.py et .env pour IP_CAMERA_URL, IP_CAMERA_SNAPSHOT_URL, etc.
"""

import sys
import os
import json
import logging
import argparse
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ajouter la racine du projet au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    ESP32_PORT,
    ACCESS_SERVER_HOST,
    FACE_CAPTURE_ATTEMPTS,
    FACE_CAPTURE_RETRY_DELAY_MS,
)
from app.services.access.ip_camera_service import IPCameraService
from app.services.access.face_recognition_service import FaceRecognitionService
from core.database.connection import DatabaseConnection

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("access_server")


# ── Validation code en base de données ───────────────────────────────────────
def _get_student_by_code(code: str) -> dict | None:
    """
    Cherche un code d'accès actif en base de données.
    Retourne le dict étudiant avec ses données de photo si trouvé, sinon None.
    Paramétrise toujours la requête pour éviter les injections SQL.
    """
    try:
        db = DatabaseConnection()

        # Schéma actuel : codes dans access_code_history (pas dans une table access_code)
        # Règle métier:
        # - code full  : valide tant que l'étudiant est dans l'année académique active
        # - code partial / legacy : validité basée sur expires_at
        # On prend la plus récente émission pour ce code.
        results = db.execute_query(
            """
            SELECT
                s.id,
                s.firstname,
                s.lastname,
                s.email,
                s.passport_photo_path,
                s.passport_photo_blob,
                s.academic_year_id,
                ach.access_code,
                ach.access_type,
                ach.expires_at
            FROM access_code_history ach
            JOIN student s ON s.id = ach.student_id
            WHERE ach.access_code = %s
              AND ach.id = (
                  SELECT ach2.id
                  FROM access_code_history ach2
                  WHERE ach2.student_id = ach.student_id
                  ORDER BY ach2.issued_at DESC, ach2.id DESC
                  LIMIT 1
              )
              AND COALESCE(s.is_active, 1) = 1
              AND (
                    (
                        ach.access_type = 'full'
                        AND s.academic_year_id IS NOT NULL
                        AND EXISTS (
                            SELECT 1 FROM academic_year ay
                            WHERE ay.academic_year_id = s.academic_year_id
                              AND ay.is_active = 1
                        )
                    )
                    OR
                    (
                        ach.access_type = 'full'
                        AND s.academic_year_id IS NULL
                        AND (ach.expires_at IS NULL OR DATE(ach.expires_at) >= CURDATE())
                    )
                    OR
                    (
                        COALESCE(ach.access_type, '') <> 'full'
                        AND (ach.expires_at IS NULL OR DATE(ach.expires_at) >= CURDATE())
                    )
                  )
            ORDER BY ach.issued_at DESC, ach.id DESC
            LIMIT 1
            """,
            (code,),
        )
        return results[0] if results else None
    except Exception as e:
        logger.error(f"Erreur validation code BD: {e}")
        return None


# ── Handler HTTP ──────────────────────────────────────────────────────────────
class AccessRequestHandler(BaseHTTPRequestHandler):
    """Traite les requêtes HTTP en provenance de l'ESP32."""

    # Injectés par run_server() avant démarrage
    camera_service: IPCameraService = None
    face_service: FaceRecognitionService = None

    # Silencer les logs HTTP par défaut (on utilise notre logger)
    def log_message(self, fmt, *args):
        logger.info("[ESP32] %s — " + fmt, self.client_address[0], *args)

    # ── Réponses ─────────────────────────────────────────────────────────────
    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── GET /status ───────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/status":
            cam_ok = False
            try:
                cam_ok = self.camera_service.check_camera()
            except Exception:
                pass
            self._send_json(200, {
                "status":  "online",
                "camera":  "ok" if cam_ok else "unavailable",
                "service": "U.O.R Access Server v2.0",
            })
        else:
            self._send_json(404, {"error": "Endpoint non trouvé"})

    # ── POST /verify_code ─────────────────────────────────────────────────────
    def do_POST(self):
        if self.path == "/verify_code":
            self._handle_verify_code()
        else:
            self._send_json(404, {"error": "Endpoint non trouvé"})

    def _handle_verify_code(self):
        """
        Flux complet d'authentification :
          1. Lire le code envoyé par l'ESP32
          2. Valider le code en base de données
          3. Capturer une image depuis la caméra IP
          4. Effectuer la reconnaissance faciale
          5. Retourner le résultat à l'ESP32
        """
        # 1. Lire et parser le payload JSON
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body.decode("utf-8"))
            code   = str(data.get("code", "")).strip()
        except Exception as e:
            logger.error(f"Payload invalide: {e}")
            self._send_json(400, {"access": "denied", "reason": "Requête invalide"})
            return

        if not code:
            self._send_json(400, {"access": "denied", "reason": "Code manquant"})
            return

        logger.info(f"Code reçu (longueur {len(code)}) — validation en cours...")

        # 2. Valider le code en base de données
        student = _get_student_by_code(code)
        if not student:
            logger.warning("Code invalide ou expiré")
            self._send_json(200, {
                "access": "denied",
                "reason": "Code invalide ou expiré",
            })
            return

        student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        logger.info(f"Code valide → {student_name} (id={student.get('id')})")

        # 3-4. Captures multiples + reconnaissance (plus robuste en conditions réelles)
        best_confidence = 0.0
        best_capture_meta = {}
        recognized = False
        confidence = 0.0
        had_frame = False

        logger.info(
            "Lancement reconnaissance faciale pour %s avec %s tentative(s)...",
            student_name,
            FACE_CAPTURE_ATTEMPTS,
        )

        for attempt in range(1, FACE_CAPTURE_ATTEMPTS + 1):
            logger.info("Capture image caméra IP... tentative %s/%s", attempt, FACE_CAPTURE_ATTEMPTS)
            frame = self.camera_service.capture_frame()
            capture_meta = self.camera_service.get_last_capture_meta()

            if capture_meta.get("discovery_message"):
                logger.info(capture_meta["discovery_message"])

            if frame is None:
                logger.warning("Capture caméra IP échouée à la tentative %s", attempt)
            else:
                had_frame = True
                recognized, confidence = self.face_service.identify_student(
                    frame=frame,
                    student=student,
                )
                if confidence >= best_confidence:
                    best_confidence = float(confidence)
                    best_capture_meta = dict(capture_meta or {})

                if recognized:
                    logger.info("Visage reconnu à la tentative %s/%s", attempt, FACE_CAPTURE_ATTEMPTS)
                    break

            # Petite pause pour laisser l'utilisateur se repositionner
            if attempt < FACE_CAPTURE_ATTEMPTS and FACE_CAPTURE_RETRY_DELAY_MS > 0:
                time.sleep(FACE_CAPTURE_RETRY_DELAY_MS / 1000.0)

        if not best_capture_meta:
            best_capture_meta = capture_meta if 'capture_meta' in locals() else {}

        # Si aucune image exploitable n'a pu être capturée
        if not had_frame:
            logger.error("Capture caméra IP échouée sur toutes les tentatives")
            self._send_json(200, {
                "access": "denied",
                "reason": "Caméra IP non disponible — réessayez",
                "camera": best_capture_meta,
            })
            return

        # 5. Retourner résultat
        if recognized:
            logger.info(f"✓ Visage reconnu : {student_name} (confiance {confidence:.2f})")
            self._send_json(200, {
                "access":     "granted",
                "name":       student_name,
                "confidence": round(confidence, 3),
                "camera":     best_capture_meta,
            })
        else:
            logger.warning(
                f"✗ Visage NON reconnu pour {student_name} "
                f"(meilleure confiance {best_confidence:.2f} après {FACE_CAPTURE_ATTEMPTS} tentative(s))"
            )
            self._send_json(200, {
                "access": "denied",
                "reason": "Visage non reconnu",
                "name":   student_name,
                "camera": best_capture_meta,
            })


# ── Démarrage serveur ─────────────────────────────────────────────────────────
def run_server(host: str = None, port: int = None):
    host = host or ACCESS_SERVER_HOST
    port = port or ESP32_PORT

    # Initialiser les services une fois (partagés entre les requêtes)
    camera_svc = IPCameraService()
    face_svc   = FaceRecognitionService()

    AccessRequestHandler.camera_service = camera_svc
    AccessRequestHandler.face_service   = face_svc

    server = HTTPServer((host, port), AccessRequestHandler)

    logger.info("=" * 60)
    logger.info("  U.O.R — Serveur d'Accès démarré")
    logger.info(f"  Écoute sur : http://{host}:{port}")
    logger.info(f"  Endpoint   : POST /verify_code")
    logger.info(f"  Santé      : GET  /status")
    logger.info("=" * 60)
    logger.info(f"Caméra IP : {camera_svc.snapshot_url or camera_svc.rtsp_url or 'non configurée'}")
    logger.info("En attente de requêtes de l'ESP32...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur (Ctrl+C)")
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="U.O.R — Serveur d'accès ESP32")
    parser.add_argument("--host", default=None, help="Interface d'écoute (défaut: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port (défaut: 5050)")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
