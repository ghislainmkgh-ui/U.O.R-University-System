"""
Service de capture d'image depuis une caméra IP
================================================
Supporte deux modes :
  - HTTP snapshot : GET sur l'URL snapshot de la caméra
      ex: http://192.168.1.50/capture  (caméra ESP32-CAM en serveur)
          http://192.168.1.50:8080/shot.jpg  (DroidCam, IP Webcam Android)
  - RTSP stream   : flux vidéo temps réel via OpenCV
      ex: rtsp://admin:password@192.168.1.50:554/stream1
          rtsp://192.168.1.50/live  (Hikvision, Dahua, etc.)

La méthode HTTP snapshot est préférée (plus rapide, moins de latence).
Le mode RTSP est utilisé en fallback automatique si le snapshot échoue.

CONFIGURATION :
  Définir dans .env :
    IP_CAMERA_SNAPSHOT_URL=http://192.168.1.50/capture
    IP_CAMERA_URL=rtsp://admin:pass@192.168.1.50:554/stream1
    IP_CAMERA_USERNAME=admin
    IP_CAMERA_PASSWORD=password
"""

import logging
import re
import socket
import time
from io import BytesIO
from ftplib import FTP
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import numpy as np
import cv2
import requests

logger = logging.getLogger(__name__)


class IPCameraService:
    """
    Capture des images depuis une caméra IP (RTSP ou HTTP snapshot).

    Ordre de priorité :
      1. HTTP snapshot (GET → image JPEG/PNG)   → rapide, ~0.2–1 s
      2. RTSP via OpenCV                         → fallback, ~1–3 s
    """

    def __init__(
        self,
        rtsp_url: str = None,
        snapshot_url: str = None,
        username: str = None,
        password: str = None,
    ):
        from config.settings import (
            IP_CAMERA_URL,
            IP_CAMERA_SNAPSHOT_URL,
            IP_CAMERA_USERNAME,
            IP_CAMERA_PASSWORD,
            IP_CAMERA_FTP_ENABLED,
            IP_CAMERA_FTP_HOST,
            IP_CAMERA_FTP_PORT,
            IP_CAMERA_FTP_PATH,
            IP_CAMERA_FTP_USERNAME,
            IP_CAMERA_FTP_PASSWORD,
            CAMERA_DEVICE_ID,
            IP_CAMERA_AUTO_DISCOVERY_ENABLED,
            IP_CAMERA_DISCOVERY_SUBNET,
            IP_CAMERA_DISCOVERY_IP_RANGE,
            IP_CAMERA_DISCOVERY_TIMEOUT,
            IP_CAMERA_DISCOVERY_MAX_WORKERS,
        )

        self.rtsp_url      = rtsp_url     or IP_CAMERA_URL
        self.snapshot_url  = snapshot_url or IP_CAMERA_SNAPSHOT_URL
        self.username      = username     or IP_CAMERA_USERNAME
        self.password      = password     or IP_CAMERA_PASSWORD
        self.ftp_enabled   = IP_CAMERA_FTP_ENABLED
        self.ftp_host      = IP_CAMERA_FTP_HOST
        self.ftp_port      = IP_CAMERA_FTP_PORT
        self.ftp_path      = IP_CAMERA_FTP_PATH
        self.ftp_username  = IP_CAMERA_FTP_USERNAME
        self.ftp_password  = IP_CAMERA_FTP_PASSWORD
        self.camera_device_id = CAMERA_DEVICE_ID
        self.auto_discovery_enabled = IP_CAMERA_AUTO_DISCOVERY_ENABLED
        self.discovery_subnet = IP_CAMERA_DISCOVERY_SUBNET
        self.discovery_ip_range = IP_CAMERA_DISCOVERY_IP_RANGE
        self.discovery_timeout = IP_CAMERA_DISCOVERY_TIMEOUT
        self.discovery_max_workers = IP_CAMERA_DISCOVERY_MAX_WORKERS
        self._last_discovery_attempt = 0.0
        self._last_capture_meta = {
            "capture_source": "",
            "camera_host": self.ftp_host or "",
            "auto_discovered": False,
            "discovery_message": "",
        }

        if not self.ftp_host:
            self.ftp_host = self._infer_camera_host()

        # Injecter credentials dans l'URL RTSP si absents
        if self.rtsp_url and self.username and "://" in self.rtsp_url:
            proto, rest = self.rtsp_url.split("://", 1)
            if "@" not in rest:
                self.rtsp_url = f"{proto}://{self.username}:{self.password}@{rest}"

        logger.info(
            f"IPCameraService initialisé — "
            f"snapshot: {'OK' if self.snapshot_url else 'non configuré'}, "
            f"RTSP: {'OK' if self.rtsp_url else 'non configuré'}, "
            f"FTP: {'OK' if self.ftp_enabled and self.ftp_host else 'non configuré'}"
        )

    # ── API publique ──────────────────────────────────────────────────────────

    def capture_frame(self) -> np.ndarray | None:
        """
        Capture une image depuis la caméra IP en parallèle.
        Lance snapshot + RTSP + FTP simultanément, utilise le plus rapide.

        Retourne : image BGR numpy array, ou None si échec.
        """
        # Première tentative rapide : paralléliser snapshot + RTSP + FTP
        frame = self._capture_frame_parallel()
        if frame is not None:
            return frame

        # Deuxième tentative: auto-découverte (plus coûteuse)
        if self.ftp_enabled and self.auto_discovery_enabled:
            discovered_host = self._discover_camera_host_via_ftp(force=True)
            if discovered_host:
                self.ftp_host = discovered_host
                frame = self._capture_ftp_snapshot()
                if frame is not None:
                    return frame

        logger.error("Impossible de capturer une image (snapshot, RTSP, FTP indisponibles)")
        return None

    def _capture_frame_parallel(self) -> np.ndarray | None:
        """Lance tous les fallbacks en parallèle, utilise le premier qui répond."""
        futures = {}
        executor = ThreadPoolExecutor(max_workers=3)
        try:
            if self.snapshot_url:
                futures[executor.submit(self._capture_http_snapshot)] = "http_snapshot"

            # Quand FTP est configuré et fonctionnel, RTSP est souvent le plus lent/inutile.
            should_try_rtsp = bool(self.rtsp_url) and not (self.ftp_enabled and self.ftp_host)
            if should_try_rtsp:
                futures[executor.submit(self._capture_rtsp_frame)] = "rtsp"

            if self.ftp_enabled and self.ftp_host:
                futures[executor.submit(self._capture_ftp_snapshot)] = "ftp"

            if not futures:
                return None

            for future in as_completed(futures, timeout=12):
                method_name = futures[future]
                try:
                    frame = future.result()
                except Exception as e:
                    logger.debug(f"Capture {method_name} échouée (parallèle): {e}")
                    continue

                if frame is not None:
                    # Annule les tâches restantes sans attendre les plus lentes.
                    for other in futures:
                        if other is not future:
                            other.cancel()
                    logger.info(f"Capture caméra réussie via {method_name} (parallèle)")
                    return frame

            return None
        except Exception as e:
            logger.debug(f"Capture parallèle: timeout/erreur globale: {e}")
            return None
        finally:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

    def _infer_camera_host(self) -> str:
        """Déduit l'hôte caméra à partir de snapshot_url ou rtsp_url si possible."""
        for url in (self.snapshot_url, self.rtsp_url):
            if not url:
                continue
            try:
                parsed = urlparse(url)
                if parsed.hostname:
                    return parsed.hostname
            except Exception:
                continue
        return ""

    def check_camera(self) -> bool:
        """Vérifie rapidement que la caméra est accessible."""
        frame = self.capture_frame()
        return frame is not None

    def get_last_capture_meta(self) -> dict:
        """Retourne les infos de la dernière capture (utile pour UI / diagnostics)."""
        return dict(self._last_capture_meta)

    # ── Méthodes privées ──────────────────────────────────────────────────────

    def _capture_http_snapshot(self) -> np.ndarray | None:
        """Capture une image via requête HTTP GET (endpoint snapshot de la caméra)."""
        try:
            auth = (self.username, self.password) if self.username else None
            resp = requests.get(self.snapshot_url, auth=auth, timeout=8, stream=True)
            resp.raise_for_status()

            # Décoder l'image JPEG/PNG reçue
            img_array = np.frombuffer(resp.content, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is None:
                logger.error("Image HTTP reçue mais décodage échoué (format non supporté ?)")
                return None

            logger.info(f"Image capturée via HTTP snapshot: {frame.shape[1]}×{frame.shape[0]} px")
            self._last_capture_meta.update({
                "capture_source": "http_snapshot",
                "camera_host": (urlparse(self.snapshot_url).hostname or "") if self.snapshot_url else "",
                "auto_discovered": False,
                "discovery_message": "",
            })
            return frame

        except requests.exceptions.Timeout:
            logger.error(f"Timeout ({8}s) connexion caméra HTTP snapshot — vérifier l'IP/port")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Caméra IP snapshot inaccessible ({self.snapshot_url})")
            return None
        except Exception as e:
            logger.error(f"Erreur HTTP snapshot: {e}")
            return None

    def _capture_rtsp_frame(self) -> np.ndarray | None:
        """Capture une frame depuis un flux RTSP via OpenCV."""
        cap = None
        try:
            logger.info(f"Connexion flux RTSP...")
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                logger.error(f"Impossible d'ouvrir le flux RTSP ({self.rtsp_url})")
                return None

            # Vider les frames en cache (obtenir une image récente)
            for _ in range(5):
                cap.grab()

            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("Lecture frame RTSP échouée")
                return None

            logger.info(f"Frame capturée via RTSP: {frame.shape[1]}×{frame.shape[0]} px")
            self._last_capture_meta.update({
                "capture_source": "rtsp",
                "camera_host": (urlparse(self.rtsp_url).hostname or "") if self.rtsp_url else "",
                "auto_discovered": False,
                "discovery_message": "",
            })
            return frame

        except Exception as e:
            logger.error(f"Erreur RTSP: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    def _capture_ftp_snapshot(self) -> np.ndarray | None:
        """Capture une image depuis un fichier JPEG via FTP (cas Yi IoT)."""
        ftp = None
        try:
            if self.auto_discovery_enabled and (
                not self.ftp_host or not self._is_tcp_port_open(self.ftp_host, self.ftp_port, timeout=0.8)
            ):
                old_host = self.ftp_host
                discovered_host = self._discover_camera_host_via_ftp()
                if discovered_host:
                    self.ftp_host = discovered_host
                    self._last_capture_meta.update({
                        "auto_discovered": True,
                        "camera_host": discovered_host,
                        "discovery_message": (
                            f"Caméra retrouvée automatiquement: {old_host or 'inconnue'} → {discovered_host}"
                        ),
                    })

            user = self.ftp_username or self.username or "root"
            pwd = self.ftp_password or self.password or ""
            ftp = FTP()
            ftp.connect(self.ftp_host, self.ftp_port, timeout=6)
            ftp.login(user, pwd)

            buf = BytesIO()
            ftp.retrbinary(f"RETR {self.ftp_path}", buf.write)
            data = buf.getvalue()

            if not data:
                logger.error("FTP snapshot vide")
                return None

            img_array = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if frame is None:
                logger.error("FTP image reçue mais décodage échoué")
                return None

            logger.info(f"Image capturée via FTP: {frame.shape[1]}×{frame.shape[0]} px")
            if not self._last_capture_meta.get("auto_discovered"):
                self._last_capture_meta["discovery_message"] = ""
            self._last_capture_meta.update({
                "capture_source": "ftp",
                "camera_host": self.ftp_host,
            })
            return frame
        except Exception as e:
            logger.error(f"Erreur FTP snapshot: {e}")
            return None
        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def _discover_camera_host_via_ftp(self, force: bool = False) -> str:
        """Découvre l'IP de la caméra Yi via scan FTP + vérification dev_id."""
        # Évite des scans trop fréquents (coûteux)
        now = time.time()
        if not force and (now - self._last_discovery_attempt) < 20:
            return ""
        self._last_discovery_attempt = now

        subnet = (self.discovery_subnet or "").strip()
        if not subnet:
            return ""

        start_ip, end_ip = self._parse_discovery_range(self.discovery_ip_range)
        if start_ip > end_ip:
            start_ip, end_ip = end_ip, start_ip

        logger.info(f"Auto-découverte Yi en cours sur {subnet}{start_ip}-{end_ip}...")

        candidates: list[str] = []
        with ThreadPoolExecutor(max_workers=max(1, self.discovery_max_workers)) as executor:
            futures = {
                executor.submit(
                    self._is_tcp_port_open,
                    f"{subnet}{ip}",
                    self.ftp_port,
                    self.discovery_timeout,
                ): f"{subnet}{ip}"
                for ip in range(start_ip, end_ip + 1)
            }

            for future in as_completed(futures):
                host = futures[future]
                try:
                    if future.result():
                        candidates.append(host)
                except Exception:
                    continue

        # Priorité à l'hôte actuel si toujours valide
        if self.ftp_host and self.ftp_host in candidates:
            candidates.remove(self.ftp_host)
            candidates.insert(0, self.ftp_host)

        for host in candidates:
            if self._is_matching_yi_camera(host):
                logger.info(f"Caméra Yi détectée automatiquement: {host}")
                return host

        logger.warning("Auto-découverte Yi: aucune caméra correspondante trouvée")
        return ""

    def _is_matching_yi_camera(self, host: str) -> bool:
        """Valide qu'un hôte FTP correspond à la caméra attendue (dev_id si disponible)."""
        ftp = None
        try:
            user = self.ftp_username or self.username or "root"
            pwd = self.ftp_password or self.password or ""

            ftp = FTP()
            ftp.connect(host, self.ftp_port, timeout=2)
            ftp.login(user, pwd)

            # Vérification de base: le fichier image attendu doit exister
            try:
                ftp.size(self.ftp_path)
            except Exception:
                return False

            # Si aucun device_id configuré, on accepte ce host FTP valide
            if not self.camera_device_id:
                return True

            # Sinon on vérifie le dev_id dans yi.conf
            buf = BytesIO()
            ftp.retrbinary("RETR /etc/jffs2/yi.conf", buf.write)
            text = buf.getvalue().decode("utf-8", errors="replace")
            found_id = ""
            for line in text.splitlines():
                if line.strip().startswith("dev_id="):
                    found_id = line.split("=", 1)[1].strip()
                    break

            if not found_id:
                return False

            return self._ids_look_same(self.camera_device_id, found_id)
        except Exception:
            return False
        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception:
                    pass

    @staticmethod
    def _parse_discovery_range(range_text: str) -> tuple[int, int]:
        """Parse un range '1-254' ou un entier simple ('42')."""
        raw = (range_text or "1-254").strip()
        if "-" in raw:
            left, right = raw.split("-", 1)
            try:
                start = max(1, min(254, int(left.strip())))
                end = max(1, min(254, int(right.strip())))
                return start, end
            except Exception:
                return 1, 254
        try:
            val = max(1, min(254, int(raw)))
            return val, val
        except Exception:
            return 1, 254

    @staticmethod
    def _is_tcp_port_open(host: str, port: int, timeout: float = 0.35) -> bool:
        s = socket.socket()
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False
        finally:
            s.close()

    @staticmethod
    def _normalize_id(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()

    @classmethod
    def _ids_look_same(cls, configured: str, found: str) -> bool:
        """Tolère de petites variations d'étiquetage entre IDs caméra."""
        a = cls._normalize_id(configured)
        b = cls._normalize_id(found)
        if not a or not b:
            return False
        if a == b:
            return True
        if a in b or b in a:
            return True
        # Heuristique robuste: suffixe identique (souvent le plus stable)
        return a[-8:] == b[-8:]
