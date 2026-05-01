"""
Mini API HTTP pour valider/rejeter les demandes d'accès via lien e-mail Super Admin.

Usage:
- GET  /health
- GET  /access-request/decision?action=approve|reject&token=...   -> page de confirmation
- POST /access-request/decision                                   -> exécute la décision

Ce service peut être déployé séparément pour permettre une validation distante
sans ouvrir l'application desktop.
"""

from flask import Flask, request, Response
from datetime import datetime
import html
import logging
import os
import sys
from werkzeug.middleware.proxy_fix import ProxyFix

# Permet d'exécuter ce script directement: python api/access_request_approval_api.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.auth.authentication_service import AuthenticationService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
auth_service = AuthenticationService()


def _normalize_action(action: str) -> str:
    val = (action or "").strip().lower()
    return val if val in {"approve", "reject"} else ""


def _page(title: str, body_html: str, status: int = 200) -> Response:
    content = f"""
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#f5f7fb; color:#1f2937; margin:0; }}
    .wrap {{ max-width: 680px; margin: 42px auto; padding: 0 16px; }}
    .card {{ background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:24px; box-shadow:0 10px 20px rgba(0,0,0,.04); }}
    h1 {{ margin:0 0 8px 0; font-size:24px; }}
    p {{ line-height:1.55; }}
    .muted {{ color:#6b7280; font-size:14px; }}
    .btn {{ border:0; border-radius:10px; padding:10px 16px; font-weight:700; cursor:pointer; }}
    .btn-approve {{ background:#059669; color:#fff; }}
    .btn-reject {{ background:#dc2626; color:#fff; }}
    .row {{ margin-top:16px; display:flex; gap:10px; align-items:center; }}
    .pill {{ display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; }}
    .ok {{ background:#dcfce7; color:#166534; }}
    .ko {{ background:#fee2e2; color:#991b1b; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      {body_html}
      <p class="muted">U.O.R • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
  </div>
</body>
</html>
""".strip()
    return Response(content, status=status, mimetype="text/html")


@app.get("/health")
def health() -> Response:
    return _page(
        "U.O.R Access Approval API",
        "<h1>Service opérationnel</h1><p>La validation Super Admin par e-mail est active.</p>",
        status=200,
    )


@app.get("/access-request/decision")
def decision_confirm() -> Response:
    token = (request.args.get("token") or "").strip()
    action = _normalize_action(request.args.get("action"))

    if not token or not action:
        return _page(
            "Lien invalide",
            "<h1>❌ Lien invalide</h1><p>Le lien est incomplet ou incorrect.</p>",
            status=400,
        )

    action_label = "validation" if action == "approve" else "rejet"
    action_btn = "Valider cette demande" if action == "approve" else "Rejeter cette demande"
    action_cls = "btn-approve" if action == "approve" else "btn-reject"
    badge_cls = "ok" if action == "approve" else "ko"

    body = f"""
<h1>Confirmer la {action_label}</h1>
<p>Vous allez <strong>{html.escape(action_label)}</strong> la demande d'accès.</p>
<p><span class="pill {badge_cls}">{'APPROUVER' if action == 'approve' else 'REJETER'}</span></p>
<form method="post" action="/access-request/decision">
  <input type="hidden" name="token" value="{html.escape(token)}" />
  <input type="hidden" name="action" value="{html.escape(action)}" />
  <div class="row">
    <button class="btn {action_cls}" type="submit">{html.escape(action_btn)}</button>
  </div>
</form>
<p class="muted">Ce lien est à usage unique.</p>
""".strip()

    return _page("Confirmation décision", body)


@app.post("/access-request/decision")
def decision_apply() -> Response:
    token = (request.form.get("token") or request.args.get("token") or "").strip()
    action = _normalize_action(request.form.get("action") or request.args.get("action"))

    if not token or not action:
        return _page(
            "Données invalides",
            "<h1>❌ Données invalides</h1><p>Action ou jeton manquant.</p>",
            status=400,
        )

    reviewer = f"email_link:{request.remote_addr or 'unknown'}"
    ok, msg = auth_service.process_access_request_token_decision(
        token=token,
        action=action,
        reviewer_identifier=reviewer,
    )

    if ok:
        icon = "✅"
        title = "Décision enregistrée"
        badge = "ok"
    else:
        icon = "❌"
        title = "Impossible de traiter la décision"
        badge = "ko"

    body = f"""
<h1>{icon} {html.escape(title)}</h1>
<p><span class="pill {badge}">{'SUCCÈS' if ok else 'ECHEC'}</span></p>
<p>{html.escape(msg or '')}</p>
""".strip()

    return _page(title, body, status=200 if ok else 400)


if __name__ == "__main__":
    logger.info("Démarrage API approbation demandes d'accès (U.O.R)")
    host = os.getenv("ACCESS_APPROVAL_API_HOST", "0.0.0.0")
    port = int(os.getenv("ACCESS_APPROVAL_API_PORT", "5002"))
    debug = os.getenv("ACCESS_APPROVAL_API_DEBUG", "False").strip().lower() == "true"

    logger.info(f"Access approval API listening on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
