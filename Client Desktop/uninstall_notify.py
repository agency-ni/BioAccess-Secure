"""
uninstall_notify.py — BioAccess Secure
Appelé par installerdesktop.bat lors de la désinstallation.

Usage : python uninstall_notify.py

Affiche une boîte de dialogue demandant le mot de passe de l'employé,
puis envoie POST /api/v1/auth/device-uninstall au backend.
Supprime device.id et cache/ après confirmation.
"""

import json
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent.absolute()
DEVICE_FILE = SCRIPT_DIR / "device.id"
CACHE_DIR   = SCRIPT_DIR / "cache"

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


def _get_api_url() -> str:
    env_file = SCRIPT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            if line.startswith("API_BASE_URL="):
                return line.split("=", 1)[1].strip()
    return "http://localhost:5000"


def run_uninstall_dialog():
    root = tk.Tk()
    root.withdraw()

    # Vérifier que device.id existe
    if not DEVICE_FILE.exists():
        messagebox.showinfo(
            "BioAccess — Désinstallation",
            "Aucun appareil enregistré sur cette machine. Désinstallation directe.",
            parent=root,
        )
        root.destroy()
        return True

    try:
        device_data = json.loads(DEVICE_FILE.read_text(encoding='utf-8'))
    except Exception:
        root.destroy()
        return True

    device_id = device_data.get('device_id', '').strip()
    if not device_id:
        root.destroy()
        return True

    # Demander confirmation
    confirmed = messagebox.askyesno(
        "BioAccess Secure — Désinstallation",
        "Vous êtes sur le point de désinstaller BioAccess Secure.\n\n"
        "Cette action sera enregistrée et notifiée à votre administrateur.\n\n"
        "Souhaitez-vous continuer ?",
        icon="warning",
        parent=root,
    )
    if not confirmed:
        root.destroy()
        return False

    # Demander le mot de passe
    password = simpledialog.askstring(
        "Authentification requise",
        "Entrez votre mot de passe pour valider la désinstallation :",
        show="*",
        parent=root,
    )
    if not password:
        messagebox.showwarning(
            "Désinstallation annulée",
            "Mot de passe non fourni — désinstallation annulée.",
            parent=root,
        )
        root.destroy()
        return False

    # Appeler le backend
    if REQUESTS_OK:
        try:
            api_url = _get_api_url()
            r = requests.post(
                f"{api_url}/api/v1/auth/device-uninstall",
                json={
                    'device_id': device_id,
                    'password': password,
                    'reason': 'Désinstallation par l\'employé',
                },
                timeout=8,
            )
            if r.ok:
                data = r.json()
                messagebox.showinfo(
                    "BioAccess — Désinstallation",
                    data.get('message', 'Désinstallation enregistrée.'),
                    parent=root,
                )
            else:
                try:
                    err = r.json().get('message') or r.json().get('error') or f"HTTP {r.status_code}"
                except Exception:
                    err = f"HTTP {r.status_code}"
                messagebox.showerror(
                    "Erreur",
                    f"Le serveur a refusé la requête : {err}\n"
                    "La désinstallation est annulée.",
                    parent=root,
                )
                root.destroy()
                return False
        except Exception as e:
            # Serveur inaccessible — on laisse quand même désinstaller avec avertissement
            messagebox.showwarning(
                "Serveur inaccessible",
                f"Impossible de contacter le serveur ({e}).\n"
                "La désinstallation sera enregistrée localement.",
                parent=root,
            )

    # Nettoyer les fichiers locaux
    try:
        if DEVICE_FILE.exists():
            DEVICE_FILE.unlink()
    except Exception:
        pass
    try:
        import shutil
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR, ignore_errors=True)
    except Exception:
        pass

    messagebox.showinfo(
        "BioAccess — Désinstallation",
        "Données locales supprimées. La désinstallation peut continuer.",
        parent=root,
    )
    root.destroy()
    return True


if __name__ == "__main__":
    ok = run_uninstall_dialog()
    sys.exit(0 if ok else 1)
