#!/usr/bin/env python3
"""
Point d'entrée principal de l'application BioAccess Secure
"""

import os
from app import create_app

app = create_app()

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