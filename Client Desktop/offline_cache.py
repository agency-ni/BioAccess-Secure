"""
offline_cache.py — BioAccess Secure
Cache local chiffré pour l'authentification en mode hors-ligne.

Format du cache (cache.json, chiffré avec Fernet) :
  {
    "<device_id>": {
      "user_id":       "uuid",
      "user_email":    "...",
      "user_name":     "...",
      "last_success":  "2026-05-14T10:30:00",
      "templates_hash":"sha256 des templates locaux (optionnel)",
      "expires_at":    "2026-06-13T10:30:00"   (30 jours)
    }
  }

La clé de chiffrement est dérivée du device_id + machine UUID
et stockée dans key.bin (jamais envoyée au serveur).
"""

import json
import logging
import hashlib
import platform
import uuid as _uuid_mod
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("bioaccess.offline_cache")

SCRIPT_DIR   = Path(__file__).parent.absolute()
CACHE_FILE   = SCRIPT_DIR / "cache" / "offline_cache.json"
KEY_FILE     = SCRIPT_DIR / "cache" / "key.bin"
MAX_AGE_DAYS = 30

# ── Chiffrement (Fernet si disponible, sinon XOR léger) ──────────────────────
try:
    from cryptography.fernet import Fernet
    _FERNET_OK = True
except ImportError:
    _FERNET_OK = False


def _machine_fingerprint() -> str:
    """Retourne une empreinte stable de la machine (MAC + hostname)."""
    try:
        mac = ':'.join(
            ['{:02X}'.format(((_uuid_mod.getnode() >> i) & 0xFF))
             for i in range(0, 48, 8)][::-1]
        )
        host = platform.node()
        return hashlib.sha256(f"{mac}:{host}".encode()).hexdigest()
    except Exception:
        return "fallback-fingerprint"


def _get_or_create_key() -> bytes:
    """
    Charge ou génère la clé Fernet liée à cette machine.
    La clé est stockée dans cache/key.bin.
    """
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        try:
            return KEY_FILE.read_bytes()
        except Exception:
            pass
    if _FERNET_OK:
        key = Fernet.generate_key()
    else:
        # Clé 32 octets dérivée de l'empreinte machine
        fp = _machine_fingerprint().encode()
        key = hashlib.sha256(fp).digest()
    KEY_FILE.write_bytes(key)
    return key


def _encrypt(data: str) -> bytes:
    """Chiffre une chaîne en bytes."""
    key = _get_or_create_key()
    if _FERNET_OK:
        return Fernet(key).encrypt(data.encode())
    # Fallback XOR simple
    key_bytes = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes(b ^ k for b, k in zip(data.encode(), key_bytes))


def _decrypt(data: bytes) -> str:
    """Déchiffre des bytes en chaîne."""
    key = _get_or_create_key()
    if _FERNET_OK:
        return Fernet(key).decrypt(data).decode()
    key_bytes = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes(b ^ k for b, k in zip(data, key_bytes)).decode()


# ═════════════════════════════════════════════════════════════════════════════
# OfflineCache
# ═════════════════════════════════════════════════════════════════════════════

class OfflineCache:
    """Cache local pour l'authentification hors-ligne."""

    # ── Lecture / écriture ────────────────────────────────────────────────────

    def _load(self) -> dict:
        if not CACHE_FILE.exists():
            return {}
        try:
            raw = CACHE_FILE.read_bytes()
            return json.loads(_decrypt(raw))
        except Exception as e:
            logger.debug(f"offline_cache _load: {e}")
            return {}

    def _save(self, data: dict):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            raw = _encrypt(json.dumps(data, indent=2))
            CACHE_FILE.write_bytes(raw)
        except Exception as e:
            logger.warning(f"offline_cache _save: {e}")

    # ── API publique ──────────────────────────────────────────────────────────

    def save_successful_auth(self, device_id: str, auth_response: dict):
        """
        Mémorise une authentification réussie.
        Appelé après chaque device-login réussi pour rafraîchir le cache.
        """
        cache = self._load()
        now = datetime.utcnow()
        cache[device_id] = {
            "user_id":       auth_response.get("user_id", ""),
            "user_email":    auth_response.get("user_email", ""),
            "user_name":     auth_response.get("user_name", ""),
            "last_success":  now.isoformat(),
            "expires_at":    (now + timedelta(days=MAX_AGE_DAYS)).isoformat(),
        }
        # Nettoyer les entrées expirées
        for did in list(cache.keys()):
            try:
                exp = datetime.fromisoformat(cache[did].get("expires_at", ""))
                if exp < now:
                    del cache[did]
            except Exception:
                pass
        self._save(cache)
        logger.info(f"Cache offline mis à jour pour device_id={device_id}")

    def has_valid_entry(self, device_id: str) -> bool:
        """
        Retourne True si une entrée non expirée existe pour ce device_id.
        """
        cache = self._load()
        entry = cache.get(device_id)
        if not entry:
            return False
        try:
            exp = datetime.fromisoformat(entry.get("expires_at", ""))
            return exp > datetime.utcnow()
        except Exception:
            return False

    def get_entry(self, device_id: str) -> dict:
        """
        Retourne les infos utilisateur du cache, ou {} si absent/expiré.
        """
        cache = self._load()
        entry = cache.get(device_id, {})
        if not entry:
            return {}
        try:
            exp = datetime.fromisoformat(entry.get("expires_at", ""))
            if exp < datetime.utcnow():
                return {}
        except Exception:
            return {}
        return entry

    def clear_device(self, device_id: str):
        """Supprime l'entrée d'un device (ex : après désinstallation)."""
        cache = self._load()
        if device_id in cache:
            del cache[device_id]
            self._save(cache)

    def purge_expired(self):
        """Supprime toutes les entrées expirées."""
        cache = self._load()
        now = datetime.utcnow()
        before = len(cache)
        for did in list(cache.keys()):
            try:
                exp = datetime.fromisoformat(cache[did].get("expires_at", ""))
                if exp < now:
                    del cache[did]
            except Exception:
                del cache[did]
        if len(cache) < before:
            self._save(cache)
            logger.info(f"Cache offline: {before - len(cache)} entrée(s) expirée(s) supprimée(s)")

    # ── Sync des logs offline ─────────────────────────────────────────────────

    LOG_FILE = SCRIPT_DIR / "cache" / "offline_logs.json"

    def append_offline_log(self, device_id: str, event: str, details: dict = None):
        """
        Enregistre un événement d'authentification offline.
        Sera synchronisé avec le serveur quand le réseau sera disponible.
        """
        logs = []
        if self.LOG_FILE.exists():
            try:
                logs = json.loads(self.LOG_FILE.read_text(encoding='utf-8'))
            except Exception:
                pass
        logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "event":     event,
            "details":   details or {},
            "synced":    False,
        })
        try:
            self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.LOG_FILE.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.debug(f"offline log write: {e}")

    def sync_logs(self, api_base_url: str, token: str) -> int:
        """
        Envoie les logs offline non synchronisés au backend.
        Retourne le nombre de logs synchronisés.
        """
        if not self.LOG_FILE.exists():
            return 0
        try:
            import requests as _req
            logs = json.loads(self.LOG_FILE.read_text(encoding='utf-8'))
            synced = 0
            for log in logs:
                if log.get("synced"):
                    continue
                try:
                    r = _req.post(
                        f"{api_base_url}/api/v1/logs/offline-sync",
                        json=log,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5,
                    )
                    if r.ok:
                        log["synced"] = True
                        synced += 1
                except Exception:
                    pass
            self.LOG_FILE.write_text(json.dumps(logs, indent=2), encoding='utf-8')
            logger.info(f"Logs offline synchronisés: {synced}/{len(logs)}")
            return synced
        except Exception as e:
            logger.debug(f"sync_logs: {e}")
            return 0
