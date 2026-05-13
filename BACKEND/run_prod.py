"""
Entrypoint de production officiel de BioAccess Secure.
Lancer depuis le dossier BACKEND avec : python run_prod.py

Accéder à l'application : http://localhost:5000/
"""

import os
import atexit
import signal
import sys
import threading
from app import create_app
from waitress import serve

app = create_app()

def _cleanup():
    """Nettoie les threads daemon au shutdown pour éviter _enter_buffered_busy"""
    for thread in threading.enumerate():
        if thread is not threading.main_thread() and thread.daemon:
            try:
                thread.join(timeout=0.5)
            except:
                pass

atexit.register(_cleanup)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

# ─── La route /<path:filename> est déjà définie dans app.py ───
# NE PAS LA RÉDÉFINIR ICI ───

if __name__ == '__main__':
    import webbrowser, time

    print("🚀 BioAccess Secure — Mode PRODUCTION")
    print("━" * 40)
    print(f"📍 Backend API  : http://localhost:5000/api/v1")
    print(f"🌐 Application  : http://localhost:5000/login.html")
    print(f"⛔ Debug        : désactivé")
    print("━" * 40)
    print("→  Ouverture du navigateur dans 2 secondes…")

    # Ouvre automatiquement le navigateur sur la bonne URL
    def _open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5000/login.html')
    threading.Thread(target=_open_browser, daemon=True).start()

    serve(
        app,
        host='0.0.0.0',
        port=5000,
        threads=8,
        connection_limit=200,
        channel_timeout=120
    )