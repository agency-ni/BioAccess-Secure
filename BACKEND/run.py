#!/usr/bin/env python3
"""
Point d'entrée de développement de l'application BioAccess Secure.
Utiliser seulement pour tests locaux et développement.
"""

import os
import atexit
import signal
import sys
import threading
from app import create_app

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0').lower() in ['1', 'true', 'yes']
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True,
        ssl_context=None  # À configurer avec certificat en production
    )