# BioAccess Secure - Startup Guide

## Production startup (recommended)
1. Ouvrir PowerShell ou terminal.
2. Aller dans le dossier `BACKEND` :
   ```powershell
   cd \Users\HP\Documents\BioAccess-Secure\BACKEND
   ```
3. Activer l'environnement virtuel (si nécessaire) :
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
4. Installer les dépendances si nécessaire :
   ```powershell
   pip install -r requirements.txt
   ```
5. Vérifier que PostgreSQL est démarré et que la base de données `bioaccess` existe.
6. Vérifier que `BACKEND/.env` contient bien :
   - `DATABASE_URL=postgresql://bioaccess_user:secure_password@localhost:5432/bioaccess`
   - `FLASK_ENV=production`
7. Lancer le serveur production :
   ```powershell
   python run_prod.py
   ```

## Points importants
- `BACKEND/run_prod.py` est le seul script de démarrage production officiel.
- `BACKEND/run.py` reste un script de développement local.
- Les autres scripts (`run_production.py`, `start_production.py`, `run_sqlite.py`, `create_tables.py`, `create_tables_sqlite.py`) sont conservés dans `BACKEND/legacy/` pour référence et ne doivent pas être utilisés en production.

## Frontend
- Le frontend appelle l'API sur `http://localhost:5000/api` par défaut.
- Vérifiez `FRONTEND/config.js` pour vous assurer que `API_URL` pointe sur `http://localhost:5000/api`.

## Desktop / door-system
- Le dossier `door-system` doit être configuré pour contacter l'API backend sur `http://localhost:5000`.
- Une fois le backend en production, les clients desktop et door-system peuvent s'appuyer sur cette API.
